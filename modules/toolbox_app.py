import gc
import json  # for preset loading/saving
import logging
import os
import psutil
import sys
import traceback
import types

# --- Standalone Startup & Path Fix ---
# This block runs only when the script is executed directly.
# It sets up the environment for standalone operation.
if __name__ == "__main__":
    # Adjust the Python path to include the project root, so local imports work.
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(modules_dir)
    if project_root not in sys.path:
        logging.info("--- Running Toolbox in Standalone Mode ---")
        logging.info(f"Adding project root to sys.path: {project_root}")
        sys.path.insert(0, project_root)

    # Set the GRADIO_TEMP_DIR *before* Gradio is imported.
    # This forces the standalone app to use the same temp folder as the main app.
    from modules.settings import Settings

    _settings_for_env = Settings()
    _gradio_temp_dir = _settings_for_env.get("gradio_temp_dir")
    if _gradio_temp_dir:
        os.environ["GRADIO_TEMP_DIR"] = os.path.abspath(_gradio_temp_dir)
        logging.info(
            f"Set GRADIO_TEMP_DIR for standalone mode: {os.environ['GRADIO_TEMP_DIR']}"
        )
    del _settings_for_env, _gradio_temp_dir

    # Suppress persistent Windows asyncio proactor errors when running standalone.
    if os.name == "nt":
        import asyncio
        from functools import wraps

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        def silence_event_loop_closed(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                try:
                    return func(self, *args, **kwargs)
                except RuntimeError as e:
                    if str(e) != "Event loop is closed":
                        raise

            return wrapper

        if hasattr(
            asyncio.proactor_events._ProactorBasePipeTransport, "_call_connection_lost"
        ):
            asyncio.proactor_events._ProactorBasePipeTransport._call_connection_lost = silence_event_loop_closed(
                asyncio.proactor_events._ProactorBasePipeTransport._call_connection_lost
            )

# --- Third-Party Library Imports ---
import gradio as gr  # noqa: E402
import imageio  # noqa: E402
import torch  # noqa: E402

# ruff: noqa: I001
from torchvision.transforms.functional import rgb_to_grayscale  # noqa: E402

# --- Patch for basicsr (must run after torchvision import) ---
functional_tensor_mod = types.ModuleType("functional_tensor")
setattr(functional_tensor_mod, "rgb_to_grayscale", rgb_to_grayscale)
sys.modules.setdefault(
    "torchvision.transforms.functional_tensor", functional_tensor_mod
)

# --- Local Application Imports ---
from modules.settings import Settings  # noqa: E402
from modules.toolbox.message_manager import MessageManager  # noqa: E402
from modules.toolbox.setup_ffmpeg import setup_ffmpeg  # noqa: E402
from modules.toolbox.system_monitor import SystemMonitor  # noqa: E402
from modules.toolbox.toolbox_processor import VideoProcessor  # noqa: E402
from modules.generators.base_generator import BaseModelGenerator  # noqa: E402
from modules.studio_manager import StudioManager  # noqa: E402
from modules.video_queue import JobStatus  # noqa: E402

logger = logging.getLogger(__name__)

# Attempt to import helper, with a fallback if it's missing.
try:
    from diffusers_helper.memory import cpu
except ImportError:
    logger.error(
        "WARNING: Could not import cpu from diffusers_helper.memory. Falling back to torch.device('cpu')"
    )
    cpu = torch.device("cpu")

# Check if FFmpeg is set up, if not, run the setup
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the correct path to the target bin directory.
bin_dir = os.path.join(script_dir, "toolbox", "bin")

ffmpeg_exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
ffmpeg_full_path = os.path.join(bin_dir, ffmpeg_exe_name)

# Check if the executable exists at the correct location.
if not os.path.exists(ffmpeg_full_path):
    logger.info(f"Bundled FFmpeg not found in '{bin_dir}'. Running one-time setup...")
    setup_ffmpeg()

studio_manager = StudioManager()  # Get the StudioManager instance
tb_message_mgr = MessageManager()
settings_instance = Settings()
tb_processor = VideoProcessor(
    tb_message_mgr, settings_instance
)  # Pass settings to VideoProcessor

# --- Default Filter Values ---
TB_DEFAULT_FILTER_SETTINGS = {
    "brightness": 0,
    "contrast": 1,
    "saturation": 1,
    "temperature": 0,
    "sharpen": 0,
    "blur": 0,
    "denoise": 0,
    "vignette": 0,
    "s_curve_contrast": 0,
    "film_grain_strength": 0,
}

# --- Filter Presets Handling ---
TB_BUILT_IN_PRESETS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "toolbox", "data", "filter_presets.json"
)
tb_filter_presets_data = {}  # Will be populated by _initialize_presets


def _initialize_presets():
    global tb_filter_presets_data
    default_preset_map_for_creation = {
        "none": TB_DEFAULT_FILTER_SETTINGS.copy(),
        "cinematic": {
            "brightness": -5,
            "contrast": 1.3,
            "saturation": 0.9,
            "temperature": 20,
            "vignette": 10,
            "sharpen": 1.2,
            "blur": 0,
            "denoise": 0,
            "s_curve_contrast": 15,
            "film_grain_strength": 5,
        },
        "vintage": {
            "brightness": 5,
            "contrast": 1.1,
            "saturation": 0.7,
            "temperature": 15,
            "vignette": 30,
            "sharpen": 0,
            "blur": 0.5,
            "denoise": 0,
            "s_curve_contrast": 10,
            "film_grain_strength": 10,
        },
        "cool": {
            "brightness": 0,
            "contrast": 1.2,
            "saturation": 1.1,
            "temperature": -15,
            "vignette": 0,
            "sharpen": 1.0,
            "blur": 0,
            "denoise": 0,
            "s_curve_contrast": 5,
            "film_grain_strength": 0,
        },
        "warm": {
            "brightness": 5,
            "contrast": 1.1,
            "saturation": 1.2,
            "temperature": 20,
            "vignette": 0,
            "sharpen": 0,
            "blur": 0,
            "denoise": 0,
            "s_curve_contrast": 5,
            "film_grain_strength": 0,
        },
        "dramatic": {
            "brightness": -5,
            "contrast": 1.2,
            "saturation": 0.9,
            "temperature": -10,
            "vignette": 20,
            "sharpen": 1.2,
            "blur": 0,
            "denoise": 0,
            "s_curve_contrast": 20,
            "film_grain_strength": 8,
        },
    }
    try:
        os.makedirs(os.path.dirname(TB_BUILT_IN_PRESETS_FILE), exist_ok=True)
        if not os.path.exists(TB_BUILT_IN_PRESETS_FILE):
            tb_message_mgr.add_message(
                f"Presets file not found. Creating with default presets: {TB_BUILT_IN_PRESETS_FILE}",
                "INFO",
            )
            with open(TB_BUILT_IN_PRESETS_FILE, "w") as f:
                json.dump(default_preset_map_for_creation, f, indent=4)
            tb_filter_presets_data = default_preset_map_for_creation
            tb_message_mgr.add_success("Default presets file created.")
        else:
            with open(TB_BUILT_IN_PRESETS_FILE, "r") as f:
                tb_filter_presets_data = json.load(f)
            # Ensure "none" preset always exists and uses TB_DEFAULT_FILTER_SETTINGS
            if (
                "none" not in tb_filter_presets_data
                or tb_filter_presets_data["none"] != TB_DEFAULT_FILTER_SETTINGS
            ):
                tb_filter_presets_data["none"] = TB_DEFAULT_FILTER_SETTINGS.copy()
                # Optionally re-save if "none" was missing or incorrect, or just use in-memory fix
                # with open(TB_BUILT_IN_PRESETS_FILE, 'w') as f:
                #    json.dump(tb_filter_presets_data, f, indent=4)

            tb_message_mgr.add_message(
                f"Filter presets loaded from {TB_BUILT_IN_PRESETS_FILE}.", "INFO"
            )
    except Exception as e:
        tb_message_mgr.add_error(
            f"Error with filter presets file {TB_BUILT_IN_PRESETS_FILE}: {e}. Using in-memory defaults."
        )
        tb_filter_presets_data = default_preset_map_for_creation


_initialize_presets()  # Call once when the script module is loaded


def tb_update_messages():
    return tb_message_mgr.get_messages()


def tb_update_filter_sliders_from_preset(preset_name):
    preset_settings = tb_filter_presets_data.get(preset_name)
    if not preset_settings:
        tb_message_mgr.add_warning(
            f"Preset '{preset_name}' not found. Using 'none' settings."
        )
        preset_settings = tb_filter_presets_data.get(
            "none", TB_DEFAULT_FILTER_SETTINGS.copy()
        )

    final_settings = TB_DEFAULT_FILTER_SETTINGS.copy()
    final_settings.update(preset_settings)

    ordered_values = []
    for key in TB_DEFAULT_FILTER_SETTINGS.keys():
        ordered_values.append(final_settings.get(key, TB_DEFAULT_FILTER_SETTINGS[key]))

    return tuple(ordered_values)


def tb_handle_reset_all_filters():
    tb_message_mgr.add_message("Filter sliders reset to default 'none' values.")
    none_settings_values = tb_update_filter_sliders_from_preset("none")
    return "none", "", *none_settings_values, tb_update_messages()


def tb_handle_save_user_preset(new_preset_name_str, *slider_values):
    global tb_filter_presets_data
    tb_message_mgr.clear()
    if not new_preset_name_str or not new_preset_name_str.strip():
        tb_message_mgr.add_warning("Preset name cannot be empty.")
        return gr.update(), tb_update_messages(), gr.update()

    clean_preset_name = new_preset_name_str.strip()

    if clean_preset_name.lower() == "none":
        tb_message_mgr.add_warning(
            "'none' is a protected preset and cannot be overwritten."
        )
        return gr.update(), tb_update_messages(), gr.update(value="")  # Clear input box

    new_preset_values = dict(zip(TB_DEFAULT_FILTER_SETTINGS.keys(), slider_values))
    preset_existed = clean_preset_name in tb_filter_presets_data
    tb_filter_presets_data[clean_preset_name] = new_preset_values
    try:
        with open(TB_BUILT_IN_PRESETS_FILE, "w") as f:
            json.dump(tb_filter_presets_data, f, indent=4)
        tb_message_mgr.add_success(
            f"Preset '{clean_preset_name}' {'updated' if preset_existed else 'saved'} successfully!"
        )

        updated_choices = list(tb_filter_presets_data.keys())
        if "none" in updated_choices:
            updated_choices.remove("none")
            updated_choices.sort()
            updated_choices.insert(0, "none")
        else:
            updated_choices.sort()

        return (
            gr.update(choices=updated_choices, value=clean_preset_name),
            tb_update_messages(),
            "",
        )
    except Exception as e:
        tb_message_mgr.add_error(f"Error saving preset '{clean_preset_name}': {e}")
        _initialize_presets()
        return gr.update(), tb_update_messages(), gr.update(value=new_preset_name_str)


def tb_handle_delete_user_preset(preset_name_to_delete):
    global tb_filter_presets_data
    tb_message_mgr.clear()
    if not preset_name_to_delete or not preset_name_to_delete.strip():
        tb_message_mgr.add_warning(
            "No preset name to delete (select from dropdown or type)."
        )
        return (
            gr.update(),
            tb_update_messages(),
            gr.update(),
            *tb_update_filter_sliders_from_preset("none"),
        )

    clean_preset_name = preset_name_to_delete.strip()
    if clean_preset_name.lower() == "none":
        tb_message_mgr.add_warning("'none' preset cannot be deleted.")
        return (
            gr.update(),
            tb_update_messages(),
            gr.update(value="none"),
            *tb_update_filter_sliders_from_preset("none"),
        )
    if clean_preset_name not in tb_filter_presets_data:
        tb_message_mgr.add_warning(f"Preset '{clean_preset_name}' not found.")
        return (
            gr.update(),
            tb_update_messages(),
            gr.update(),
            *tb_update_filter_sliders_from_preset("none"),
        )

    del tb_filter_presets_data[clean_preset_name]
    try:
        with open(TB_BUILT_IN_PRESETS_FILE, "w") as f:
            json.dump(tb_filter_presets_data, f, indent=4)
        tb_message_mgr.add_success(f"Preset '{clean_preset_name}' deleted.")

        updated_choices = list(tb_filter_presets_data.keys())
        if "none" in updated_choices:
            updated_choices.remove("none")
            updated_choices.sort()
            updated_choices.insert(0, "none")
        else:
            updated_choices.sort()

        sliders_reset_values = tb_update_filter_sliders_from_preset("none")
        return (
            gr.update(choices=updated_choices, value="none"),
            tb_update_messages(),
            "",
            *sliders_reset_values,
        )
    except Exception as e:
        tb_message_mgr.add_error(
            f"Error deleting preset '{clean_preset_name}' from file: {e}"
        )
        _initialize_presets()
        current_choices = list(tb_filter_presets_data.keys())
        if "none" in current_choices:
            current_choices.remove("none")
            current_choices.sort()
            current_choices.insert(0, "none")
        else:
            current_choices.sort()
        selected_val_after_error = (
            clean_preset_name if clean_preset_name in current_choices else "none"
        )
        sliders_after_error_values = tb_update_filter_sliders_from_preset(
            selected_val_after_error
        )
        return (
            gr.update(choices=current_choices, value=selected_val_after_error),
            tb_update_messages(),
            gr.update(value=selected_val_after_error),
            *sliders_after_error_values,
        )


# --- Workflow Presets Handling ---
TB_WORKFLOW_PRESETS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "toolbox",
    "data",
    "workflow_presets.json",
)
tb_workflow_presets_data = {}  # Will be populated by _initialize_workflow_presets


# This helper function creates a dictionary of all default parameter values
def _get_default_workflow_params():
    # Gets default values from filter settings and adds other op defaults
    params = TB_DEFAULT_FILTER_SETTINGS.copy()
    params.update(
        {
            "upscale_model": list(tb_processor.esrgan_upscaler.supported_models.keys())[
                0
            ]
            if tb_processor.esrgan_upscaler.supported_models
            else None,
            "upscale_factor": 2.0,
            "tile_size": 0,
            "enhance_face": False,
            "denoise_strength": 0.5,
            "upscale_use_streaming": False,
            "frames_use_streaming": False,
            "fps_mode": "No Interpolation",
            "speed_factor": 1.0,
            "loop_type": "loop",
            "num_loops": 1,
            "export_format": "MP4",
            "export_quality": 85,
            "export_max_width": 1024,
        }
    )
    return params


def _initialize_workflow_presets():
    global tb_workflow_presets_data
    # The 'None' preset stores default values for all controls and no active steps
    default_workflow_map = {
        "None": {"active_steps": [], "params": _get_default_workflow_params()}
    }
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(TB_WORKFLOW_PRESETS_FILE), exist_ok=True)
        if not os.path.exists(TB_WORKFLOW_PRESETS_FILE):
            tb_message_mgr.add_message(
                f"Workflow presets file not found. Creating with a default 'None' preset: {TB_WORKFLOW_PRESETS_FILE}",
                "INFO",
            )
            with open(TB_WORKFLOW_PRESETS_FILE, "w") as f:
                json.dump(default_workflow_map, f, indent=4)
            tb_workflow_presets_data = default_workflow_map
        else:
            with open(TB_WORKFLOW_PRESETS_FILE, "r") as f:
                tb_workflow_presets_data = json.load(f)
            # Ensure "None" preset always exists and is up-to-date
            tb_workflow_presets_data["None"] = default_workflow_map["None"]
            tb_message_mgr.add_message(
                f"Workflow presets loaded from {TB_WORKFLOW_PRESETS_FILE}.", "INFO"
            )
    except Exception as e:
        tb_message_mgr.add_error(
            f"Error with workflow presets file {TB_WORKFLOW_PRESETS_FILE}: {e}. Using in-memory defaults."
        )
        tb_workflow_presets_data = default_workflow_map


_initialize_workflow_presets()  # Call once when the script module is loaded


def tb_handle_reassemble_frames(
    frames_source_folder, output_fps, output_video_name, progress=gr.Progress()
):
    tb_message_mgr.clear()
    tb_message_mgr.add_message("Preparing to reassemble from Frames Studio...")
    if not frames_source_folder:
        tb_message_mgr.add_warning(
            "No source folder selected in the Frames Studio dropdown."
        )
        return None, tb_update_messages()

    frames_path_to_use = os.path.join(
        tb_processor.extracted_frames_target_path, frames_source_folder
    )
    source_description = f"Frames Studio folder '{frames_source_folder}'"

    if not os.path.isdir(frames_path_to_use):
        tb_message_mgr.add_error(f"Selected folder not found: {frames_path_to_use}")
        return None, tb_update_messages()

    tb_message_mgr.add_message(
        f"Attempting to reassemble frames from {source_description}."
    )
    output_video = tb_processor.tb_reassemble_frames_to_video(
        frames_path_to_use,
        output_fps,
        output_base_name_override=output_video_name,
        progress=progress,
    )
    return output_video, tb_update_messages()


def tb_handle_clear_selected_folder(selected_folder_to_delete):
    tb_message_mgr.clear()
    if not selected_folder_to_delete:
        tb_message_mgr.add_warning("No folder selected from the dropdown to delete.")
        return (
            tb_update_messages(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    tb_processor.tb_delete_extracted_frames_folder(selected_folder_to_delete)
    updated_folders = tb_processor.tb_get_extracted_frame_folders()

    # Return updates for all components: messages, dropdown, gallery, info box, and the two frame action buttons.
    return (
        tb_update_messages(),
        gr.update(choices=updated_folders, value=None),  # Update dropdown
        None,  # Clear the gallery
        None,  # Clear the info box
        gr.update(interactive=False),  # Disable save button
        gr.update(interactive=False),  # Disable delete button
    )


def tb_handle_load_frames_to_studio(selected_folder):
    tb_message_mgr.clear()
    if not selected_folder:
        tb_message_mgr.add_warning("No folder selected to load into the studio.")
        return tb_update_messages(), None, "Select a folder and click 'Load'."

    frame_files_list = tb_processor.tb_get_frames_from_folder(selected_folder)

    if not frame_files_list:
        tb_message_mgr.add_warning(f"No image files found in '{selected_folder}'.")
        return tb_update_messages(), None, "No frames found in this folder."

    tb_message_mgr.add_success(
        f"Loaded {len(frame_files_list)} frames from '{selected_folder}' into the studio."
    )
    return tb_update_messages(), frame_files_list, "Select a frame from the gallery."


def tb_handle_frame_select(evt: gr.SelectData):
    """Handles frame selection in the gallery, providing more detailed info."""
    # The gallery's select event (evt.value) is a dictionary like:
    # {'image': {'path': '...', 'url': '...'}, 'caption': None}
    if evt.value and "image" in evt.value and "path" in evt.value["image"]:
        # CORRECT WAY to access the path string
        selected_image_path = evt.value["image"]["path"]

        # Now 'selected_image_path' is a string, so os.path.basename will work correctly.
        filename = os.path.basename(selected_image_path)

        info_text = f"File: {filename}"
        try:
            # Add image dimensions to the info box for better context
            img = imageio.imread(selected_image_path)
            h, w, *_ = img.shape
            info_text += f"\nDimensions: {w}x{h}"
        except Exception as e:
            tb_message_mgr.add_warning(f"Could not read dimensions for {filename}: {e}")

        # 1. Return the info string to the gr.Textbox component.
        # 2 & 3. Return updates to enable the buttons.
        return info_text, gr.update(interactive=True), gr.update(interactive=True)
    else:
        # This part handles deselection or malformed event data
        return (
            "Select a frame...",
            gr.update(interactive=False),
            gr.update(interactive=False),
        )


def _get_frame_path_from_ui(selected_folder, frame_info_str):
    """Helper to safely parse UI components to get a full file path."""
    if not selected_folder or not frame_info_str:
        return None, "Missing folder or frame selection."

    # Extract filename from the first line of the info string "File: frame_0000.png"
    first_line = frame_info_str.splitlines()[0]
    if not first_line.startswith("File: "):
        return None, "Invalid frame info format."

    filename_to_process = first_line.replace("File: ", "").strip()
    full_path = os.path.join(
        tb_processor.extracted_frames_target_path, selected_folder, filename_to_process
    )
    return full_path, None


def tb_handle_delete_and_refresh_gallery(selected_folder, frame_info_str):
    """
    Deletes the selected frame, gets the updated frame list, and explicitly
    determines the next frame to select to create a seamless workflow.
    """
    if not selected_folder:
        tb_message_mgr.add_warning("Cannot delete frame: No folder selected.")
        return gr.update(), gr.update(), gr.update(), gr.update(), tb_update_messages()

    full_path_to_delete, error = _get_frame_path_from_ui(
        selected_folder, frame_info_str
    )
    if error:
        tb_message_mgr.add_error(f"Could not identify frame to delete: {error}")
        return gr.update(), gr.update(), gr.update(), gr.update(), tb_update_messages()

    old_frame_list = tb_processor.tb_get_frames_from_folder(selected_folder)
    try:
        deleted_index = old_frame_list.index(full_path_to_delete)
    except ValueError:
        tb_message_mgr.add_error(
            f"Consistency error: Frame '{os.path.basename(full_path_to_delete)}' not found in its folder's frame list before deletion."
        )
        # As a fallback, just delete and refresh to a safe state
        tb_processor.tb_delete_single_frame(full_path_to_delete)
        updated_frame_list_fallback = tb_processor.tb_get_frames_from_folder(
            selected_folder
        )
        return (
            updated_frame_list_fallback,
            "Select a frame...",
            gr.update(interactive=False),
            gr.update(interactive=False),
            tb_update_messages(),
        )

    tb_processor.tb_delete_single_frame(
        full_path_to_delete
    )  # This logs the success message
    new_frame_list = tb_processor.tb_get_frames_from_folder(selected_folder)

    if not new_frame_list:
        # The folder is now empty
        info_text = "All frames have been deleted."
        return (
            [],
            info_text,
            gr.update(interactive=False),
            gr.update(interactive=False),
            tb_update_messages(),
        )
    else:
        # Determine the index of the next frame to highlight.
        # This keeps the selection at the same position, or on the new last item if the old last item was deleted.
        next_selection_index = min(deleted_index, len(new_frame_list) - 1)

        # Explicitly generate the info for the frame that will now be selected.
        new_selected_path = new_frame_list[next_selection_index]
        filename = os.path.basename(new_selected_path)
        info_text = f"File: {filename}"
        try:
            img = imageio.imread(new_selected_path)
            h, w, *_ = img.shape
            info_text += f"\nDimensions: {w}x{h}"
        except Exception as e:
            tb_message_mgr.add_warning(
                f"Could not read dimensions for new selection {filename}: {e}"
            )

        # Return all the new state information to update the UI in one go.
        return (
            new_frame_list,
            info_text,
            gr.update(interactive=True),
            gr.update(interactive=True),
            tb_update_messages(),
        )


def tb_handle_save_selected_frame(selected_folder, frame_info_str):
    """Handler for the save button. Calls the backend processor."""
    tb_message_mgr.clear()
    full_path, error = _get_frame_path_from_ui(selected_folder, frame_info_str)
    if error:
        tb_message_mgr.add_error(error)
        return error, tb_update_messages()

    status_message = tb_processor.tb_save_single_frame(full_path)
    # The message is generated inside the processor, we just need to return it.
    return status_message, tb_update_messages()


# --- END: Frames Studio Handlers ---

# --- START: Workflow Preset Handlers ---


def tb_handle_save_workflow_preset(preset_name, active_steps, *params):
    global tb_workflow_presets_data
    tb_message_mgr.clear()

    if not preset_name or not preset_name.strip():
        tb_message_mgr.add_warning("Workflow Preset name cannot be empty.")
        return gr.update(), gr.update(value=preset_name), tb_update_messages()

    clean_name = preset_name.strip()
    # This key list MUST match the order of components in _ALL_PIPELINE_PARAMS_COMPONENTS_
    param_keys = [
        # Upscale
        "upscale_model",
        "upscale_factor",
        "tile_size",
        "enhance_face",
        "denoise_strength",
        "upscale_use_streaming",
        # Frame Adjust
        "fps_mode",
        "speed_factor",
        "frames_use_streaming",
        # Loop
        "loop_type",
        "num_loops",
        # Filters (using the ordered keys from the constant)
        *list(TB_DEFAULT_FILTER_SETTINGS.keys()),
        # Export
        "export_format",
        "export_quality",
        "export_max_width",
    ]

    # Pack the parameters into a dictionary
    params_dict = dict(zip(param_keys, params))

    new_preset_data = {"active_steps": active_steps, "params": params_dict}

    preset_existed = clean_name in tb_workflow_presets_data
    tb_workflow_presets_data[clean_name] = new_preset_data

    try:
        with open(TB_WORKFLOW_PRESETS_FILE, "w") as f:
            json.dump(tb_workflow_presets_data, f, indent=4)

        tb_message_mgr.add_success(
            f"Workflow Preset '{clean_name}' {'updated' if preset_existed else 'saved'} successfully!"
        )

        # Update dropdown choices
        updated_choices = sorted(
            [k for k in tb_workflow_presets_data.keys() if k != "None"]
        )
        updated_choices.insert(0, "None")

        return (
            gr.update(choices=updated_choices, value=clean_name),
            "",
            tb_update_messages(),
        )

    except Exception as e:
        tb_message_mgr.add_error(f"Error saving workflow preset '{clean_name}': {e}")
        # Revert to last known good state
        _initialize_workflow_presets()
        return gr.update(), gr.update(value=preset_name), tb_update_messages()

    except Exception as e:
        tb_message_mgr.add_error(f"Error saving workflow preset '{clean_name}': {e}")
        # Revert to last known good state
        _initialize_workflow_presets()
        return gr.update(), gr.update(value=preset_name), tb_update_messages()


def tb_handle_load_workflow_preset(preset_name):
    tb_message_mgr.clear()
    preset_data = tb_workflow_presets_data.get(preset_name)

    if not preset_data:
        tb_message_mgr.add_warning(
            f"Workflow preset '{preset_name}' not found. Loading 'None' state."
        )
        preset_data = tb_workflow_presets_data.get("None")

    # Get the default parameter structure to ensure all keys are present
    final_params = _get_default_workflow_params()
    # Update with the loaded preset's parameters
    final_params.update(preset_data.get("params", {}))

    active_steps = preset_data.get("active_steps", [])

    # The order of values returned MUST match the order of components in the event handler's output list
    ordered_values = [
        # Checkbox
        active_steps,
        # Upscale
        final_params["upscale_model"],
        final_params["upscale_factor"],
        final_params["tile_size"],
        final_params["enhance_face"],
        final_params["denoise_strength"],
        final_params["upscale_use_streaming"],
        # Frame Adjust
        final_params["fps_mode"],
        final_params["speed_factor"],
        final_params["frames_use_streaming"],
        # Loop
        final_params["loop_type"],
        final_params["num_loops"],
        # Filters (must be in the same order as _ORDERED_FILTER_SLIDERS_)
        final_params["brightness"],
        final_params["contrast"],
        final_params["saturation"],
        final_params["temperature"],
        final_params["sharpen"],
        final_params["blur"],
        final_params["denoise"],
        final_params["vignette"],
        final_params["s_curve_contrast"],
        final_params["film_grain_strength"],
        # Export
        final_params["export_format"],
        final_params["export_quality"],
        final_params["export_max_width"],
    ]

    tb_message_mgr.add_message(f"Loaded workflow preset: '{preset_name}'")
    # Also return the preset name to the input box, and the updated messages
    return preset_name, *ordered_values, tb_update_messages()


def tb_handle_delete_workflow_preset(preset_name):
    global tb_workflow_presets_data
    tb_message_mgr.clear()

    if not preset_name or not preset_name.strip():
        tb_message_mgr.add_warning("No workflow preset name provided to delete.")
        # The number of outputs for an event handler MUST be consistent.
        # There are 28 outputs: dropdown, namebox, chkbox, 24 params, message.
        # The star-expansion covers the chkbox (1) + params (24) = 25 components.
        return gr.update(), gr.update(), *([gr.update()] * 25), tb_update_messages()

    clean_name = preset_name.strip()
    if clean_name == "None":
        tb_message_mgr.add_warning("'None' preset cannot be deleted.")
        return (
            gr.update(value="None"),
            gr.update(),
            *([gr.update()] * 25),
            tb_update_messages(),
        )

    if clean_name not in tb_workflow_presets_data:
        tb_message_mgr.add_warning(f"Workflow preset '{clean_name}' not found.")
        return gr.update(), gr.update(), *([gr.update()] * 25), tb_update_messages()

    del tb_workflow_presets_data[clean_name]

    try:
        with open(TB_WORKFLOW_PRESETS_FILE, "w") as f:
            json.dump(tb_workflow_presets_data, f, indent=4)
        tb_message_mgr.add_success(f"Workflow preset '{clean_name}' deleted.")

        updated_choices = sorted(
            [k for k in tb_workflow_presets_data.keys() if k != "None"]
        )
        updated_choices.insert(0, "None")

        # After deleting, load the "None" state to get the reset values
        none_state_outputs = tb_handle_load_workflow_preset("None")

        # The rest of the values come from the 'load' function, but we skip its first value (which was also for the textbox)
        return (
            gr.update(choices=updated_choices, value="None"),
            "",
            *none_state_outputs[1:],
        )

    except Exception as e:
        tb_message_mgr.add_error(f"Error deleting workflow preset '{clean_name}': {e}")
        _initialize_workflow_presets()  # Revert
        # On error, we don't know the state, so just update the messages
        return (
            gr.update(),
            gr.update(value=clean_name),
            *([gr.update()] * 25),
            tb_update_messages(),
        )


# --- END: New Workflow Preset Handlers ---

# Process steps, in the order they always run. Keys match the "active_steps"
# names stored in workflow presets.
TB_STEPS = [
    ("upscale", "Upscale"),
    ("frames", "Frame rate & speed"),
    ("filters", "Filters"),
    ("loop", "Loop"),
    ("export", "Export"),
]


def _tb_input_paths(single_video_path, batch_files):
    if batch_files:
        return [f if isinstance(f, str) else f.name for f in batch_files]
    return [single_video_path] if single_video_path else []


def tb_process_summary(single_video_path, batch_files, *steps_on):
    """The line above Run, and whether Run can be pressed."""
    names = [label for (_, label), on in zip(TB_STEPS, steps_on) if on]
    paths = _tb_input_paths(single_video_path, batch_files)
    if not paths:
        text, ready = "Add a video to start.", False
    elif not names:
        text, ready = "Switch on at least one step.", False
    else:
        target = f"{len(paths)} videos" if len(paths) > 1 else "1 video"
        text, ready = f"{' → '.join(names)} · {target}", True
    label = f"Run on {len(paths)} videos" if len(paths) > 1 else "Run"
    return (
        gr.update(value=text),
        gr.update(interactive=ready, value=label),
    )


def tb_handle_start_pipeline(
    single_video_path,
    batch_files,
    upscale_on,
    frames_on,
    filters_on,
    loop_on,
    export_on,
    # Upscale
    model_key,
    output_scale_factor,
    tile_size,
    enhance_face,
    denoise_strength,
    upscale_use_streaming,
    # Frame rate & speed
    fps_mode,
    speed_factor,
    frames_use_streaming,
    # Loop
    loop_type,
    num_loops,
    # Filters
    brightness,
    contrast,
    saturation,
    temperature,
    sharpen,
    blur,
    denoise,
    vignette,
    s_curve_contrast,
    film_grain_strength,
    # Export
    export_format,
    export_quality,
    export_max_width,
    export_name,
    progress=gr.Progress(),
):
    tb_message_mgr.clear()
    paths = _tb_input_paths(single_video_path, batch_files)
    if not paths:
        tb_message_mgr.add_warning("Add a video first.")
        return gr.update(), tb_update_messages()

    operations = []
    if upscale_on:
        operations.append(
            {
                "name": "upscale",
                "params": {
                    "model_key": model_key,
                    "output_scale_factor_ui": float(output_scale_factor),
                    "tile_size": int(tile_size),
                    "enhance_face": enhance_face,
                    "denoise_strength_ui": denoise_strength,
                    "use_streaming": upscale_use_streaming,
                },
            }
        )
    if frames_on:
        operations.append(
            {
                "name": "frame_adjust",
                "params": {
                    "target_fps_mode": fps_mode,
                    "speed_factor": speed_factor,
                    "use_streaming": frames_use_streaming,
                },
            }
        )
    if filters_on:
        operations.append(
            {
                "name": "filters",
                "params": {
                    "brightness": brightness,
                    "contrast": contrast,
                    "saturation": saturation,
                    "temperature": temperature,
                    "sharpen": sharpen,
                    "blur": blur,
                    "denoise": denoise,
                    "vignette": vignette,
                    "s_curve_contrast": s_curve_contrast,
                    "film_grain_strength": film_grain_strength,
                },
            }
        )
    if loop_on:
        operations.append(
            {"name": "loop", "params": {"loop_type": loop_type, "num_loops": num_loops}}
        )
    if export_on:
        export_params = {
            "export_format": export_format,
            "quality_slider": int(export_quality),
            "max_width": int(export_max_width),
        }
        # A custom name only makes sense for one video; a batch keeps its names.
        if export_name and export_name.strip() and len(paths) == 1:
            export_params["output_base_name_override"] = export_name.strip()
        operations.append({"name": "export", "params": export_params})

    if not operations:
        tb_message_mgr.add_warning("Switch on at least one step.")
        return gr.update(), tb_update_messages()

    final_video_path = tb_processor.tb_process_video_batch(
        paths, {"operations": operations}, progress
    )
    return final_video_path, tb_update_messages()


def tb_get_model_info_and_update_scale_slider(model_key_selected: str):
    native_scale = 2.0
    slider_min = 1.0
    slider_max = 2.0
    slider_step = 0.05
    slider_default_value = 2.0
    model_info_text = "Select a model."
    slider_label = "Scale"

    denoise_slider_visible = False
    denoise_slider_value = 0.5

    if (
        model_key_selected
        and model_key_selected in tb_processor.esrgan_upscaler.supported_models
    ):
        model_details = tb_processor.esrgan_upscaler.supported_models[
            model_key_selected
        ]
        fetched_native_scale = model_details.get("scale")
        description = model_details.get("description", "No description available.")

        if isinstance(fetched_native_scale, (int, float)) and fetched_native_scale > 0:
            native_scale = float(fetched_native_scale)
            slider_max = native_scale
            slider_default_value = native_scale
            slider_min = 1.0

            if native_scale >= 4.0:
                slider_step = 0.1
            elif native_scale >= 2.0:
                slider_step = 0.05

        model_info_text = f"{description}"
        slider_label = f"Scale (model is {native_scale:g}×)"

        if model_key_selected == "RealESR-general-x4v3":
            denoise_slider_visible = True

    model_info_update = gr.update(info=model_info_text)
    outscale_slider_update = gr.update(
        minimum=slider_min,
        maximum=slider_max,
        step=slider_step,
        value=slider_default_value,
        label=slider_label,
    )
    denoise_slider_update = gr.update(
        visible=denoise_slider_visible, value=denoise_slider_value
    )

    return model_info_update, outscale_slider_update, denoise_slider_update


def tb_handle_delete_studio_transformer():
    tb_message_mgr.clear()
    tb_message_mgr.add_message(
        "Attempting to directly access and delete Studio transformer..."
    )
    logger.info("Attempting to directly access and delete Studio transformer...")
    log_messages_from_action = []

    studio_module_instance = None
    if "__main__" in sys.modules:
        # __main__ will always exist
        studio_module_instance = sys.modules["__main__"]
        logger.info("Found studio context in __main__.")
    elif "studio" in sys.modules:
        studio_module_instance = sys.modules["studio"]
        logger.info("Found studio context in sys.modules['studio'].")

    # Ensure any existing LoRAs are unloaded from the current generator
    if (
        studio_manager.current_generator is None
        or studio_manager.current_generator.transformer is None
    ):
        logger.error("Current transformer is None.")
        tb_message_mgr.add_message(
            "ERROR: Current transformer is None. Nothing to delete."
        )
        tb_message_mgr.add_warning("Deletion Failed: Current transformer is None.")
        return tb_update_messages()

    if studio_module_instance is None:
        logger.error("Could not find the 'studio' module's active context.")
        tb_message_mgr.add_message(
            "ERROR: Could not find the 'studio' module's active context in sys.modules."
        )
        tb_message_mgr.add_error("Deletion Failed: Studio module context not found.")
        return tb_update_messages()

    job_queue_instance = studio_manager.job_queue or getattr(
        studio_module_instance, "job_queue", None
    )

    if job_queue_instance:
        current_job_in_queue = job_queue_instance.current_job or getattr(
            job_queue_instance, "current_job", None
        )
        if (
            current_job_in_queue
            and hasattr(current_job_in_queue, "status")
            and current_job_in_queue.status == JobStatus.RUNNING
        ):
            tb_message_mgr.add_warning(
                "Cannot unload model: A video generation job is currently running."
            )
            tb_message_mgr.add_message(
                "Please wait for the current job to complete or cancel it first using the main interface."
            )
            logger.error(
                "Cannot unload model: A job is currently running in the queue."
            )
            return tb_update_messages()

    # should be able to remove the getattr() call here, since we are directly accessing the studio_manager
    generator_object_to_delete = studio_manager.current_generator or getattr(
        studio_module_instance, "current_generator", None
    )
    logger.info(
        f"Direct access: generator_object_to_delete is {type(generator_object_to_delete)}, id: {id(generator_object_to_delete)}"
    )

    if generator_object_to_delete is not None:
        model_name_str = "Unknown Model"

        try:
            if isinstance(generator_object_to_delete, BaseModelGenerator):
                model_name_str = generator_object_to_delete.get_model_name()
            # No need for attribute acrobatics here
            elif hasattr(generator_object_to_delete, "get_model_name") and callable(
                generator_object_to_delete.get_model_name
            ):
                model_name_str = generator_object_to_delete.get_model_name()
            elif (
                hasattr(generator_object_to_delete, "transformer")
                and generator_object_to_delete.transformer is not None
            ):
                model_name_str = (
                    generator_object_to_delete.transformer.__class__.__name__
                )
            else:
                model_name_str = generator_object_to_delete.__class__.__name__
        except Exception:
            pass

        tb_message_mgr.add_message(f" Deletion of '{model_name_str}' initiated.")
        log_messages_from_action.append(
            f" Found active generator: {model_name_str}. Preparing for deletion."
        )
        logger.info(
            f"Found active generator: {model_name_str}. Preparing for deletion."
        )

        try:
            if isinstance(generator_object_to_delete, BaseModelGenerator):
                logger.debug("   - LoRAs: Unloading from transformer...")
                generator_object_to_delete.unload_loras()
            # No need for attribute acrobatics here
            elif hasattr(generator_object_to_delete, "unload_loras") and callable(
                generator_object_to_delete.unload_loras
            ):
                logger.debug("   - LoRAs: Unloading from transformer...")
                generator_object_to_delete.unload_loras()
            else:
                log_messages_from_action.append(
                    "    - LoRAs: No unload method found or not applicable."
                )

            if (
                isinstance(generator_object_to_delete, BaseModelGenerator)
                and generator_object_to_delete.transformer is not None
            ):
                transformer_object_ref = generator_object_to_delete.transformer
                transformer_name_for_log = transformer_object_ref.__class__.__name__
                logger.debug(
                    f"   - Transformer ({transformer_name_for_log}): Preparing for memory operations."
                )
                if transformer_object_ref.device != cpu:
                    logger.debug(
                        f"   - Transformer ({transformer_name_for_log}): Moving to CPU..."
                    )
                    transformer_object_ref.to(cpu)  # type: ignore
                    log_messages_from_action.append("    - Transformer moved to CPU.")
                    logger.debug(
                        f"   - Transformer ({transformer_name_for_log}): Moved to CPU."
                    )
                else:
                    log_messages_from_action.append("    - Transformer already on CPU.")
                    logger.debug(
                        f"   - Transformer ({transformer_name_for_log}): Already on CPU."
                    )

                logger.debug(
                    f"   - Transformer ({transformer_name_for_log}): Removing attribute from generator..."
                )
                generator_object_to_delete.transformer = None  # type: ignore
                del transformer_object_ref
                log_messages_from_action.append("    - Transformer reference deleted.")
                logger.debug(
                    f"   - Transformer ({transformer_name_for_log}): Reference deleted."
                )

            # No need for attribute acrobatics here
            if (
                hasattr(generator_object_to_delete, "transformer")
                and generator_object_to_delete.transformer is not None
            ):
                transformer_object_ref = generator_object_to_delete.transformer
                transformer_name_for_log = transformer_object_ref.__class__.__name__
                logger.debug(
                    f"   - Transformer ({transformer_name_for_log}): Preparing for memory operations."
                )

                if (
                    hasattr(transformer_object_ref, "device")
                    and transformer_object_ref.device != cpu
                ):
                    if hasattr(transformer_object_ref, "to") and callable(
                        transformer_object_ref.to
                    ):
                        try:
                            logger.debug(
                                f"   - Transformer ({transformer_name_for_log}): Moving to CPU..."
                            )
                            transformer_object_ref.to(cpu)
                            log_messages_from_action.append(
                                "    - Transformer moved to CPU."
                            )
                            logger.debug(
                                f"   - Transformer ({transformer_name_for_log}): Moved to CPU."
                            )
                        except Exception as e_cpu:
                            error_msg_cpu = f"    - Transformer ({transformer_name_for_log}): Move to CPU FAILED: {e_cpu}"
                            log_messages_from_action.append(error_msg_cpu)
                            logger.error(error_msg_cpu)
                    else:
                        log_messages_from_action.append(
                            f"    - Transformer ({transformer_name_for_log}): Cannot move to CPU, 'to' method not found."
                        )
                        logger.debug(
                            f"   - Transformer ({transformer_name_for_log}): Cannot move to CPU, 'to' method not found."
                        )
                elif (
                    hasattr(transformer_object_ref, "device")
                    and transformer_object_ref.device == cpu
                ):
                    log_messages_from_action.append("    - Transformer already on CPU.")
                    logger.debug(
                        f"   - Transformer ({transformer_name_for_log}): Already on CPU."
                    )
                else:
                    log_messages_from_action.append(
                        "    - Transformer: Could not determine device or move to CPU."
                    )
                    logger.debug(
                        f"   - Transformer ({transformer_name_for_log}): Could not determine device or move to CPU."
                    )

                logger.debug(
                    f"   - Transformer ({transformer_name_for_log}): Removing attribute from generator..."
                )
                generator_object_to_delete.transformer = None
                logger.debug(
                    f"   - Transformer ({transformer_name_for_log}): Deleting Python reference..."
                )
                del transformer_object_ref
                log_messages_from_action.append("    - Transformer reference deleted.")
                logger.debug(
                    f"   - Transformer ({transformer_name_for_log}): Reference deleted."
                )
            else:
                log_messages_from_action.append(
                    "    - Transformer: Not found or already unloaded."
                )
                logger.debug("   - Transformer: Not found or already unloaded.")

            generator_class_name_for_log = generator_object_to_delete.__class__.__name__
            logger.info(
                f"   - Model Generator ({generator_class_name_for_log}): Setting global reference to None..."
            )
            if studio_manager.current_generator is not None:
                studio_manager.unset_current_generator()
                log_messages_from_action.append(
                    "    - 'current_generator' in studio manager set to None."
                )
                logger.info(
                    "   - Global 'current_generator' in studio manager successfully set to None."
                )
            else:
                setattr(studio_module_instance, "current_generator", None)
                log_messages_from_action.append(
                    "    - 'current_generator' in studio module set to None."
                )
                logger.info(
                    "   - Global 'current_generator' in studio module successfully set to None."
                )

            logger.info(
                f"   - Model Generator ({generator_class_name_for_log}): Deleting local Python reference..."
            )
            del generator_object_to_delete
            logger.info(
                f"   - Model Generator ({generator_class_name_for_log}): Python reference deleted."
            )

            logger.debug(
                "   - System: Performing garbage collection and CUDA cache clearing."
            )
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            log_messages_from_action.append("    - GC and CUDA cache cleared.")
            logger.debug("   - System: GC and CUDA cache clear completed.")

            log_messages_from_action.append(
                f"✅ Deletion of '{model_name_str}' completed successfully from toolbox."
            )
            tb_message_mgr.add_success(
                f"Deletion of '{model_name_str}' initiated from toolbox."
            )

        except Exception as e_del:
            error_msg_del = f"Error during deletion process: {e_del}"
            log_messages_from_action.append(f"    - {error_msg_del}")
            logger.error(f"   - {error_msg_del}")
            traceback.print_exc()
            tb_message_mgr.add_error(f"Deletion Error: {e_del}")
    else:
        tb_message_mgr.add_message("ℹ️ No active generator found. Nothing to delete.")
        logger.info("No active generator found via direct access. Nothing to delete.")

    for msg_item in log_messages_from_action:
        tb_message_mgr.add_message(msg_item)

    return tb_update_messages()


def tb_handle_manually_save_video(temp_video_path_from_component):
    tb_message_mgr.clear()
    if not temp_video_path_from_component:
        tb_message_mgr.add_warning("No video in the output player to save.")
        return temp_video_path_from_component, tb_update_messages()

    copied_path = tb_processor.tb_copy_video_to_permanent_storage(
        temp_video_path_from_component
    )

    if copied_path and os.path.abspath(copied_path) != os.path.abspath(
        temp_video_path_from_component
    ):
        tb_message_mgr.add_success("Video successfully copied to permanent storage.")

    return temp_video_path_from_component, tb_update_messages()


def tb_handle_clear_temp_files():
    tb_message_mgr.clear()

    # The processor function now returns a complete summary string.
    cleanup_summary = tb_processor.tb_clear_temporary_files()

    # Add the summary to the message manager to be displayed in the console.
    tb_message_mgr.add_message(cleanup_summary)

    # Return None to clear the video player and the updated messages.
    return None, tb_update_messages()


def tb_handle_use_processed_as_input(processed_video_path):
    if not processed_video_path:
        tb_message_mgr.add_warning("No processed video available to use as input.")
        # Return updates for all 3 outputs, changing nothing.
        return gr.update(), tb_update_messages(), gr.update()
    else:
        tb_message_mgr.add_message("Moved processed video to input.")
        # Return new value for input, messages, and None to clear analysis.
        return processed_video_path, tb_update_messages(), None


def tb_handle_join_videos(
    video_files_list, custom_output_name, progress=gr.Progress()
):  # Add new parameter
    tb_message_mgr.clear()

    if not video_files_list:
        tb_message_mgr.add_warning("No video files were uploaded to join.")
        return None, tb_update_messages()

    video_paths = [file.name for file in video_files_list]

    # Pass the custom name to the processor
    output_video = tb_processor.tb_join_videos(
        video_paths, custom_output_name, progress
    )
    return output_video, tb_update_messages()


def tb_get_formatted_toolbar_stats():
    """
    Returns a CSS <style> snippet that updates variables for the static toolbar stat cards.
    This avoids DOM replacement and prevents flashing.
    """
    # Defaults
    ram_pct = 0
    ram_value_str = "N/A"
    vram_pct = 0
    vram_value_str = "N/A"
    gpu_load_pct = 0
    gpu_value_str = "N/A"

    try:
        # RAM via psutil
        ram_info_psutil = psutil.virtual_memory()
        ram_used_gb = ram_info_psutil.used / (1024**3)
        ram_total_gb = ram_info_psutil.total / (1024**3)
        ram_pct = int(round(ram_info_psutil.percent))
        ram_value_str = f"{ram_used_gb:.1f}/{round(ram_total_gb)}GB ({ram_pct}%)"

        # GPU/VRAM via nvidia-smi if available
        if torch.cuda.is_available():
            _, nvidia_metrics, _ = SystemMonitor.get_nvidia_gpu_info()
            if nvidia_metrics:
                vram_used = nvidia_metrics.get("memory_used_gb", 0.0)
                vram_total = nvidia_metrics.get("memory_total_gb", 0.0)
                vram_pct = (
                    int(round((vram_used / vram_total) * 100)) if vram_total else 0
                )
                vram_value_str = f"{vram_used:.1f}/{round(vram_total)}GB ({vram_pct}%)"

                temp = nvidia_metrics.get("temperature", 0.0)
                load = nvidia_metrics.get("utilization", 0.0)
                gpu_load_pct = int(round(load))
                gpu_value_str = f"{temp:.0f}°C {gpu_load_pct}%"
    except Exception as e:
        logger.error(
            f"Error getting system stats values for toolbar (from toolbox_app.py): {e}"
        )

    css_vars = f"""
<style id="toolbar-stats-vars">
#toolbar-stats-container{{
  --ram-fill: {ram_pct}%;
  --ram-text: '{ram_value_str}';
  --vram-fill: {vram_pct}%;
  --vram-text: '{vram_value_str}';
  --gpu-fill: {gpu_load_pct}%;
  --gpu-text: '{gpu_value_str}';
}}
</style>
""".strip()

    return gr.update(value=css_vars)


# --- Gradio Interface ---


def _tb_preset_choices(data, none_key, none_label):
    names = sorted(k for k in data if k != none_key)
    return [(none_label, none_key), *[(n, n) for n in names]]


def _tb_relabel(update, data, none_key, none_label):
    """Keep the friendly "none" label when a preset handler resets the choices."""
    if isinstance(update, dict) and "choices" in update:
        update["choices"] = _tb_preset_choices(data, none_key, none_label)
    return update


def _tb_step_card(key, title, note):
    """A step: a switch in the header, its settings shown only while it's on."""
    with gr.Group(elem_classes="step-card", elem_id=f"step-{key}"):
        switch = gr.Checkbox(
            label=title, info=note, value=False, elem_classes="step-switch"
        )
        body = gr.Column(visible=False, elem_classes="step-body")
    switch.change(
        lambda on: gr.update(visible=on), switch, body, show_progress="hidden"
    )
    return switch, body


def tb_create_video_toolbox_ui():
    initial_autosave_state = settings_instance.get("toolbox_autosave_enabled", True)
    tb_processor.set_autosave_mode(initial_autosave_state)

    upscale_models = list(tb_processor.esrgan_upscaler.supported_models.keys())
    default_model = upscale_models[0] if upscale_models else None
    model_info, scale_init, denoise_init = tb_get_model_info_and_update_scale_slider(
        default_model
    )

    with gr.Column(elem_id="tools") as tb_toolbox_ui_main_container:
        tb_mode = gr.Radio(
            ["Process", "Join clips", "Edit frames"],
            value="Process",
            show_label=False,
            container=False,
            elem_id="tools-mode",
        )
        with gr.Row(equal_height=False):
            # ------------------------------------------------ left: the work
            with gr.Column(scale=5, elem_id="tools-main"):
                with gr.Column(elem_id="tools-input") as tb_input_col:
                    tb_input_video_component = gr.Video(
                        label="Input",
                        autoplay=True,
                        sources=["upload"],
                        elem_classes="video-size",
                        elem_id="toolbox-video-player",
                    )
                    with gr.Accordion(
                        "Details", open=False, elem_classes="quiet-accordion"
                    ):
                        tb_video_analysis_output = gr.Textbox(
                            show_label=False,
                            container=False,
                            lines=8,
                            interactive=False,
                            elem_classes="analysis-box",
                        )

                # Process: one list of steps, run top to bottom
                with gr.Column(visible=True) as tb_process_col:
                    with gr.Accordion(
                        "Batch: process several videos instead",
                        open=False,
                        elem_classes="quiet-accordion",
                    ):
                        tb_batch_input_files = gr.File(
                            show_label=False,
                            file_count="multiple",
                            file_types=["video"],
                            type="filepath",
                        )
                        gr.Markdown(
                            "While files are here, Run uses them instead of the input "
                            "above. Results go to a new folder in `saved_videos`.",
                            elem_classes="field-note",
                        )

                    with gr.Row(elem_classes="steps-head", equal_height=True):
                        gr.Markdown("### Steps", elem_classes="section-title")
                        tb_workflow_preset_select = gr.Dropdown(
                            choices=_tb_preset_choices(
                                tb_workflow_presets_data, "None", "No recipe"
                            ),
                            value="None",
                            allow_custom_value=True,
                            show_label=False,
                            container=False,
                            scale=2,
                            elem_id="recipe-select",
                        )
                        tb_workflow_save_btn = gr.Button(
                            "Save recipe", size="sm", scale=0, min_width=100
                        )
                        tb_workflow_delete_btn = gr.Button(
                            "Delete",
                            size="sm",
                            scale=0,
                            min_width=70,
                            interactive=False,
                        )
                    with gr.Row(
                        visible=False, elem_classes="inline-form"
                    ) as tb_workflow_delete_row:
                        tb_workflow_delete_text = gr.Markdown("")
                        tb_workflow_delete_yes = gr.Button(
                            "Delete", variant="stop", size="sm", scale=0
                        )
                        tb_workflow_delete_no = gr.Button("Keep it", size="sm", scale=0)

                    # Upscale
                    tb_upscale_on, body = _tb_step_card(
                        "upscale", "Upscale", "Real-ESRGAN, with optional face restore"
                    )
                    with body:
                        with gr.Row():
                            tb_upscale_model_select = gr.Dropdown(
                                choices=upscale_models,
                                value=default_model,
                                label="Model",
                                info=model_info.get("info"),
                            )
                            tb_upscale_factor_slider = gr.Slider(
                                minimum=scale_init.get("minimum", 1.0),
                                maximum=scale_init.get("maximum", 2.0),
                                step=scale_init.get("step", 0.05),
                                value=scale_init.get("value", 2.0),
                                label=scale_init.get("label", "Scale"),
                            )
                        with gr.Row():
                            tb_upscale_tile_size_radio = gr.Radio(
                                choices=[("Off", 0), ("512", 512), ("256", 256)],
                                value=0,
                                label="Tiling",
                                info="Use if you run out of VRAM. Slower.",
                            )
                            tb_denoise_strength_slider = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                step=0.01,
                                value=denoise_init.get("value", 0.5),
                                label="Denoise",
                                info="0 = strongest",
                                visible=denoise_init.get("visible", False),
                            )
                        with gr.Row():
                            tb_upscale_enhance_face_checkbox = gr.Checkbox(
                                label="Restore faces (GFPGAN)", value=False
                            )
                            tb_upscale_use_streaming_checkbox = gr.Checkbox(
                                label="Low memory",
                                info="Streams frames. For long or 4K clips.",
                                value=False,
                            )

                    # Frame rate & speed
                    tb_frames_on, body = _tb_step_card(
                        "frames",
                        "Frame rate & speed",
                        "RIFE interpolation, speed up or slow down",
                    )
                    with body:
                        with gr.Row():
                            tb_process_fps_mode = gr.Radio(
                                choices=[
                                    ("Off", "No Interpolation"),
                                    ("2×", "2x Frames"),
                                    ("4×", "4x Frames"),
                                ],
                                value="No Interpolation",
                                label="Interpolate",
                                info="More frames, smoother motion",
                            )
                            tb_process_speed_factor = gr.Slider(
                                minimum=0.25,
                                maximum=4.0,
                                step=0.05,
                                value=1.0,
                                label="Speed",
                                info="Below 1 slows down, above 1 speeds up",
                            )
                        tb_frames_use_streaming_checkbox = gr.Checkbox(
                            label="Low memory",
                            info="Streams frames. Speed is ignored in this mode.",
                            value=False,
                        )

                    # Filters
                    tb_filters_on, body = _tb_step_card(
                        "filters", "Filters", "Colour, contrast, sharpness, grain"
                    )
                    with body:
                        with gr.Row(elem_classes="preset-line", equal_height=True):
                            tb_filter_preset_select = gr.Dropdown(
                                choices=_tb_preset_choices(
                                    tb_filter_presets_data, "none", "None"
                                ),
                                value="none",
                                allow_custom_value=True,
                                label="Look",
                                info="Pick one to load, or type a name and save.",
                                scale=3,
                            )
                            tb_save_preset_btn = gr.Button(
                                "Save", size="sm", scale=0, min_width=70
                            )
                            tb_delete_preset_btn = gr.Button(
                                "Delete",
                                size="sm",
                                scale=0,
                                min_width=70,
                                interactive=False,
                            )
                            tb_reset_filters_btn = gr.Button(
                                "Reset", size="sm", scale=0, min_width=70
                            )
                        with gr.Row():
                            tb_filter_brightness = gr.Slider(
                                -100,
                                100,
                                step=1,
                                label="Brightness",
                                value=TB_DEFAULT_FILTER_SETTINGS["brightness"],
                            )
                            tb_filter_contrast = gr.Slider(
                                0,
                                3,
                                step=0.05,
                                label="Contrast",
                                value=TB_DEFAULT_FILTER_SETTINGS["contrast"],
                            )
                        with gr.Row():
                            tb_filter_saturation = gr.Slider(
                                0,
                                3,
                                step=0.05,
                                label="Saturation",
                                info="0 is greyscale",
                                value=TB_DEFAULT_FILTER_SETTINGS["saturation"],
                            )
                            tb_filter_temperature = gr.Slider(
                                -100,
                                100,
                                step=1,
                                label="Temperature",
                                info="Negative is cooler, positive warmer",
                                value=TB_DEFAULT_FILTER_SETTINGS["temperature"],
                            )
                        with gr.Accordion(
                            "Detail & texture",
                            open=False,
                            elem_classes="quiet-accordion",
                        ):
                            with gr.Row():
                                tb_filter_sharpen = gr.Slider(
                                    0,
                                    5,
                                    step=0.1,
                                    label="Sharpen",
                                    value=TB_DEFAULT_FILTER_SETTINGS["sharpen"],
                                )
                                tb_filter_blur = gr.Slider(
                                    0,
                                    5,
                                    step=0.1,
                                    label="Blur",
                                    value=TB_DEFAULT_FILTER_SETTINGS["blur"],
                                )
                            with gr.Row():
                                tb_filter_denoise = gr.Slider(
                                    0,
                                    10,
                                    step=0.1,
                                    label="Denoise",
                                    value=TB_DEFAULT_FILTER_SETTINGS["denoise"],
                                )
                                tb_filter_s_curve_contrast = gr.Slider(
                                    0,
                                    100,
                                    step=1,
                                    label="S-curve contrast",
                                    value=TB_DEFAULT_FILTER_SETTINGS[
                                        "s_curve_contrast"
                                    ],
                                )
                            with gr.Row():
                                tb_filter_vignette = gr.Slider(
                                    0,
                                    100,
                                    step=1,
                                    label="Vignette",
                                    value=TB_DEFAULT_FILTER_SETTINGS["vignette"],
                                )
                                tb_filter_film_grain_strength = gr.Slider(
                                    0,
                                    50,
                                    step=1,
                                    label="Film grain",
                                    value=TB_DEFAULT_FILTER_SETTINGS[
                                        "film_grain_strength"
                                    ],
                                )

                    # Loop
                    tb_loop_on, body = _tb_step_card(
                        "loop", "Loop", "Repeat or ping-pong the clip"
                    )
                    with body:
                        with gr.Row():
                            tb_loop_type_select = gr.Radio(
                                choices=[("Loop", "loop"), ("Ping-pong", "ping-pong")],
                                value="loop",
                                label="Mode",
                            )
                            tb_num_loops_slider = gr.Slider(
                                minimum=1,
                                maximum=10,
                                step=1,
                                value=1,
                                label="Extra plays",
                                info="1 plays the clip twice",
                            )

                    # Export
                    tb_export_on, body = _tb_step_card(
                        "export", "Export", "MP4, WebM or GIF, resized and compressed"
                    )
                    with body:
                        with gr.Row():
                            tb_export_format_radio = gr.Radio(
                                ["MP4", "WebM", "GIF"],
                                value="MP4",
                                label="Format",
                                info="GIF is silent and always saved",
                            )
                            tb_export_quality_slider = gr.Slider(
                                0,
                                100,
                                value=85,
                                step=1,
                                label="Quality",
                                info="80–90 is a good balance",
                            )
                        with gr.Row():
                            tb_export_resize_slider = gr.Slider(
                                256,
                                2048,
                                value=1024,
                                step=64,
                                label="Max width",
                                info="Keeps the aspect ratio",
                            )
                            tb_export_name_input = gr.Textbox(
                                label="File name",
                                placeholder="optional",
                                info="Single video only",
                            )

                    with gr.Row(elem_id="tools-run", equal_height=True):
                        tb_run_summary = gr.Markdown(
                            "Add a video to start.", elem_classes="run-summary"
                        )
                        tb_start_pipeline_btn = gr.Button(
                            "Run",
                            variant="primary",
                            interactive=False,
                            scale=0,
                            min_width=160,
                            elem_id="toolbox-start-pipeline-btn",
                        )

                # Join clips
                with gr.Column(visible=False) as tb_join_col:
                    tb_join_videos_input = gr.File(
                        label="Clips, in order",
                        file_count="multiple",
                        file_types=["video"],
                    )
                    gr.Markdown(
                        "Different sizes and audio are matched automatically.",
                        elem_classes="field-note",
                    )
                    with gr.Row(equal_height=True):
                        tb_join_video_name_input = gr.Textbox(
                            show_label=False,
                            container=False,
                            placeholder="File name (optional)",
                        )
                        tb_join_videos_btn = gr.Button(
                            "Join", variant="primary", scale=0, min_width=160
                        )

                # Edit frames
                with gr.Column(visible=False) as tb_frames_col:
                    gr.Markdown("**1 · Extract** the input video to images")
                    with gr.Row(elem_classes="align-end"):
                        tb_extract_rate_slider = gr.Number(
                            label="Every Nth frame",
                            info="1 keeps every frame. Long or 4K clips use a lot of disk.",
                            value=1,
                            minimum=1,
                            step=1,
                        )
                        tb_extract_frames_btn = gr.Button(
                            "Extract", variant="primary", scale=0, min_width=120
                        )

                    gr.Markdown("**2 · Edit** remove bad frames, save stills")
                    with gr.Row(elem_classes="align-end"):
                        tb_extracted_folders_dropdown = gr.Dropdown(
                            choices=tb_processor.tb_get_extracted_frame_folders(),
                            value=None,
                            label="Frames folder",
                            scale=3,
                            elem_id="frames-folder",
                        )
                        tb_refresh_extracted_folders_btn = gr.Button(
                            "↻", size="sm", scale=0, min_width=40
                        )
                        tb_clear_selected_folder_btn = gr.Button(
                            "Delete folder",
                            size="sm",
                            scale=0,
                            min_width=110,
                            interactive=False,
                        )
                    with gr.Row(
                        visible=False, elem_classes="inline-form"
                    ) as tb_folder_delete_row:
                        tb_folder_delete_text = gr.Markdown("")
                        tb_folder_delete_yes = gr.Button(
                            "Delete", variant="stop", size="sm", scale=0
                        )
                        tb_folder_delete_no = gr.Button("Keep it", size="sm", scale=0)
                    with gr.Column(elem_id="gallery-scroll-wrapper"):
                        tb_frames_gallery = gr.Gallery(
                            show_label=False,
                            elem_id="toolbox_frames_gallery",
                            columns=8,
                            object_fit="contain",
                            preview=False,
                        )
                    with gr.Row(elem_classes="align-end"):
                        tb_frame_info_box = gr.Textbox(
                            interactive=False,
                            show_label=False,
                            container=False,
                            placeholder="Pick a folder, then click a frame.",
                            lines=2,
                            scale=3,
                        )
                        tb_save_selected_frame_btn = gr.Button(
                            "Save still",
                            size="sm",
                            scale=0,
                            min_width=100,
                            interactive=False,
                        )
                        tb_delete_selected_frame_btn = gr.Button(
                            "Delete frame",
                            size="sm",
                            scale=0,
                            min_width=110,
                            interactive=False,
                        )

                    gr.Markdown("**3 · Rebuild** the video from what's left")
                    with gr.Row(elem_classes="align-end"):
                        tb_reassemble_output_fps = gr.Number(
                            label="FPS", value=30, minimum=1, step=1, scale=1
                        )
                        tb_reassemble_video_name_input = gr.Textbox(
                            label="File name", placeholder="optional", scale=2
                        )
                        tb_reassemble_frames_btn = gr.Button(
                            "Rebuild", variant="primary", scale=0, min_width=120
                        )

            # ---------------------------------------------- right: the result
            with gr.Column(scale=4, elem_id="tools-result"):
                tb_processed_video_output = gr.Video(
                    label="Result",
                    autoplay=True,
                    interactive=False,
                    elem_classes="video-size",
                )
                with gr.Row(elem_classes="action-row"):
                    tb_use_processed_as_input_btn = gr.Button("Use as input", size="sm")
                    tb_manual_save_btn = gr.Button(
                        "Save", size="sm", visible=not initial_autosave_state
                    )
                    tb_open_folder_button = gr.Button("Open folder", size="sm")
                tb_autosave_checkbox = gr.Checkbox(
                    label="Save results automatically",
                    info="Off keeps results in a temp folder until you press Save.",
                    value=initial_autosave_state,
                )
                tb_message_output = gr.Textbox(
                    label="Log",
                    lines=8,
                    max_lines=8,
                    interactive=False,
                    autoscroll=True,
                    elem_classes="message-box",
                    value=tb_update_messages,
                )
                with gr.Row(elem_classes="action-row"):
                    tb_delete_studio_transformer_btn = gr.Button(
                        "Free VRAM: unload video model", size="sm"
                    )
                    tb_clear_temp_button = gr.Button("Clear temp files", size="sm")

    # ------------------------------------------------------------- events

    def on_mode(mode):
        return (
            gr.update(visible=mode != "Join clips"),
            gr.update(visible=mode == "Process"),
            gr.update(visible=mode == "Join clips"),
            gr.update(visible=mode == "Edit frames"),
        )

    tb_mode.change(
        on_mode,
        tb_mode,
        [tb_input_col, tb_process_col, tb_join_col, tb_frames_col],
        show_progress="hidden",
    )

    _ORDERED_FILTER_SLIDERS_ = [
        tb_filter_brightness,
        tb_filter_contrast,
        tb_filter_saturation,
        tb_filter_temperature,
        tb_filter_sharpen,
        tb_filter_blur,
        tb_filter_denoise,
        tb_filter_vignette,
        tb_filter_s_curve_contrast,
        tb_filter_film_grain_strength,
    ]
    # Order matches the param keys in tb_handle_save_workflow_preset
    _ALL_PIPELINE_PARAMS_COMPONENTS_ = [
        tb_upscale_model_select,
        tb_upscale_factor_slider,
        tb_upscale_tile_size_radio,
        tb_upscale_enhance_face_checkbox,
        tb_denoise_strength_slider,
        tb_upscale_use_streaming_checkbox,
        tb_process_fps_mode,
        tb_process_speed_factor,
        tb_frames_use_streaming_checkbox,
        tb_loop_type_select,
        tb_num_loops_slider,
        *_ORDERED_FILTER_SLIDERS_,
        tb_export_format_radio,
        tb_export_quality_slider,
        tb_export_resize_slider,
    ]
    step_switches = [
        tb_upscale_on,
        tb_frames_on,
        tb_filters_on,
        tb_loop_on,
        tb_export_on,
    ]
    step_keys = [key for key, _ in TB_STEPS]

    # Run
    summary_inputs = [tb_input_video_component, tb_batch_input_files, *step_switches]
    for comp in summary_inputs:
        comp.change(
            tb_process_summary,
            summary_inputs,
            [tb_run_summary, tb_start_pipeline_btn],
            show_progress="hidden",
        )
    tb_start_pipeline_btn.click(
        fn=tb_handle_start_pipeline,
        inputs=[
            tb_input_video_component,
            tb_batch_input_files,
            *step_switches,
            *_ALL_PIPELINE_PARAMS_COMPONENTS_,
            tb_export_name_input,
        ],
        outputs=[tb_processed_video_output, tb_message_output],
    )

    # Recipes (workflow presets): every step's settings and which steps are on
    def load_recipe(name):
        _, steps, *values, messages = tb_handle_load_workflow_preset(name)
        switches = [key in (steps or []) for key in step_keys]
        return (*switches, *values, messages, gr.update(interactive=name != "None"))

    recipe_load_outputs = [
        *step_switches,
        *_ALL_PIPELINE_PARAMS_COMPONENTS_,
        tb_message_output,
        tb_workflow_delete_btn,
    ]
    tb_workflow_preset_select.select(
        load_recipe, tb_workflow_preset_select, recipe_load_outputs
    )
    tb_workflow_preset_select.change(
        lambda name: gr.update(
            interactive=bool(name)
            and name in tb_workflow_presets_data
            and name != "None"
        ),
        tb_workflow_preset_select,
        tb_workflow_delete_btn,
        show_progress="hidden",
    )

    def save_recipe(name, *values):
        switches, params = values[: len(step_keys)], values[len(step_keys) :]
        steps = [key for key, on in zip(step_keys, switches) if on]
        if (name or "").strip() == "None":
            tb_message_mgr.clear()
            tb_message_mgr.add_warning("Type a name for the recipe first.")
            return gr.update(), tb_update_messages(), gr.update()
        dropdown, _, messages = tb_handle_save_workflow_preset(name, steps, *params)
        dropdown = _tb_relabel(dropdown, tb_workflow_presets_data, "None", "No recipe")
        saved = (name or "").strip() in tb_workflow_presets_data
        return dropdown, messages, gr.update(interactive=saved)

    tb_workflow_save_btn.click(
        save_recipe,
        [tb_workflow_preset_select, *step_switches, *_ALL_PIPELINE_PARAMS_COMPONENTS_],
        [tb_workflow_preset_select, tb_message_output, tb_workflow_delete_btn],
    )
    tb_workflow_delete_btn.click(
        lambda name: (gr.update(visible=True), f"Delete the recipe **{name}**?"),
        tb_workflow_preset_select,
        [tb_workflow_delete_row, tb_workflow_delete_text],
    )
    tb_workflow_delete_no.click(
        lambda: gr.update(visible=False), None, tb_workflow_delete_row
    )

    def delete_recipe(name):
        dropdown, _, steps, *values, messages = tb_handle_delete_workflow_preset(name)
        dropdown = _tb_relabel(dropdown, tb_workflow_presets_data, "None", "No recipe")
        if isinstance(steps, list):
            switches = [key in steps for key in step_keys]
        else:
            switches = [gr.update()] * len(step_keys)
        return (
            gr.update(visible=False),
            dropdown,
            *switches,
            *values,
            messages,
            gr.update(interactive=False),
        )

    tb_workflow_delete_yes.click(
        delete_recipe,
        tb_workflow_preset_select,
        [tb_workflow_delete_row, tb_workflow_preset_select, *recipe_load_outputs],
    )

    # Upscale
    tb_upscale_model_select.change(
        fn=tb_get_model_info_and_update_scale_slider,
        inputs=[tb_upscale_model_select],
        outputs=[
            tb_upscale_model_select,
            tb_upscale_factor_slider,
            tb_denoise_strength_slider,
        ],
    )

    # Filter looks
    tb_filter_preset_select.select(
        lambda name: (
            *tb_update_filter_sliders_from_preset(name),
            gr.update(interactive=name != "none"),
        ),
        tb_filter_preset_select,
        [*_ORDERED_FILTER_SLIDERS_, tb_delete_preset_btn],
    )

    def save_look(name, *values):
        dropdown, messages, _ = tb_handle_save_user_preset(name, *values)
        dropdown = _tb_relabel(dropdown, tb_filter_presets_data, "none", "None")
        saved = (name or "").strip() in tb_filter_presets_data
        return dropdown, messages, gr.update(interactive=saved and name != "none")

    tb_save_preset_btn.click(
        save_look,
        [tb_filter_preset_select, *_ORDERED_FILTER_SLIDERS_],
        [tb_filter_preset_select, tb_message_output, tb_delete_preset_btn],
    )

    def delete_look(name):
        dropdown, messages, _, *values = tb_handle_delete_user_preset(name)
        dropdown = _tb_relabel(dropdown, tb_filter_presets_data, "none", "None")
        return dropdown, messages, *values, gr.update(interactive=False)

    tb_delete_preset_btn.click(
        delete_look,
        tb_filter_preset_select,
        [
            tb_filter_preset_select,
            tb_message_output,
            *_ORDERED_FILTER_SLIDERS_,
            tb_delete_preset_btn,
        ],
    )

    def reset_look():
        dropdown, _, *values, messages = tb_handle_reset_all_filters()
        return dropdown, *values, messages, gr.update(interactive=False)

    tb_reset_filters_btn.click(
        reset_look,
        None,
        [
            tb_filter_preset_select,
            *_ORDERED_FILTER_SLIDERS_,
            tb_message_output,
            tb_delete_preset_btn,
        ],
    )

    # Input and result
    def on_input(video_path, mode):
        tb_message_mgr.clear()
        if not video_path:
            return None, tb_update_messages(), gr.update()
        # A video sent here (e.g. from the Library) shouldn't land in hidden Join
        return (
            tb_processor.tb_analyze_video_input(video_path),
            tb_update_messages(),
            gr.update(value="Process") if mode == "Join clips" else gr.update(),
        )

    tb_input_video_component.change(
        on_input,
        [tb_input_video_component, tb_mode],
        [tb_video_analysis_output, tb_message_output, tb_mode],
        show_progress="hidden",
    )
    tb_use_processed_as_input_btn.click(
        fn=lambda path: tb_handle_use_processed_as_input(path)[:2],
        inputs=[tb_processed_video_output],
        outputs=[tb_input_video_component, tb_message_output],
    )
    tb_manual_save_btn.click(
        fn=tb_handle_manually_save_video,
        inputs=[tb_processed_video_output],
        outputs=[tb_processed_video_output, tb_message_output],
    )

    def on_autosave(on):
        settings_instance.set("toolbox_autosave_enabled", on)
        tb_processor.set_autosave_mode(on)
        return gr.update(visible=not on), tb_update_messages()

    tb_autosave_checkbox.change(
        on_autosave, tb_autosave_checkbox, [tb_manual_save_btn, tb_message_output]
    )
    tb_open_folder_button.click(
        fn=lambda: tb_processor.tb_open_output_folder() or tb_update_messages(),
        outputs=[tb_message_output],
    )
    tb_clear_temp_button.click(
        fn=tb_handle_clear_temp_files,
        outputs=[tb_processed_video_output, tb_message_output],
    )
    tb_delete_studio_transformer_btn.click(
        fn=tb_handle_delete_studio_transformer, outputs=[tb_message_output]
    )

    # Join
    tb_join_videos_btn.click(
        fn=tb_handle_join_videos,
        inputs=[tb_join_videos_input, tb_join_video_name_input],
        outputs=[tb_processed_video_output, tb_message_output],
    )

    # Edit frames
    frame_buttons = [tb_save_selected_frame_btn, tb_delete_selected_frame_btn]

    def extract(video_path, rate, progress=gr.Progress()):
        tb_message_mgr.clear()
        folder = tb_processor.tb_extract_frames(video_path, int(rate), progress)
        folders = tb_processor.tb_get_extracted_frame_folders()
        name = os.path.basename(folder) if folder else None
        return (
            gr.update(choices=folders, value=name if name in folders else None),
            tb_update_messages(),
        )

    tb_extract_frames_btn.click(
        extract,
        [tb_input_video_component, tb_extract_rate_slider],
        [tb_extracted_folders_dropdown, tb_message_output],
    )
    tb_refresh_extracted_folders_btn.click(
        lambda current: gr.update(
            choices=(folders := tb_processor.tb_get_extracted_frame_folders()),
            value=current if current in folders else None,
        ),
        tb_extracted_folders_dropdown,
        tb_extracted_folders_dropdown,
    )

    def open_folder(folder):
        if not folder:
            return (
                None,
                "",
                gr.update(interactive=False),
                *[gr.update(interactive=False)] * 2,
                gr.update(visible=False),
            )
        messages, frames, info = tb_handle_load_frames_to_studio(folder)
        return (
            frames,
            info if frames else "No frames in this folder.",
            gr.update(interactive=True),
            *[gr.update(interactive=False)] * 2,
            gr.update(visible=False),
        )

    tb_extracted_folders_dropdown.change(
        open_folder,
        tb_extracted_folders_dropdown,
        [
            tb_frames_gallery,
            tb_frame_info_box,
            tb_clear_selected_folder_btn,
            *frame_buttons,
            tb_folder_delete_row,
        ],
    )
    tb_clear_selected_folder_btn.click(
        lambda folder: (
            gr.update(visible=True),
            f"Delete **{folder}** and all its frames?",
        ),
        tb_extracted_folders_dropdown,
        [tb_folder_delete_row, tb_folder_delete_text],
    )
    tb_folder_delete_no.click(
        lambda: gr.update(visible=False), None, tb_folder_delete_row
    )
    tb_folder_delete_yes.click(
        fn=lambda folder: (
            gr.update(visible=False),
            *tb_handle_clear_selected_folder(folder),
        ),
        inputs=[tb_extracted_folders_dropdown],
        outputs=[
            tb_folder_delete_row,
            tb_message_output,
            tb_extracted_folders_dropdown,
            tb_frames_gallery,
            tb_frame_info_box,
            *frame_buttons,
        ],
    )
    tb_frames_gallery.select(
        fn=tb_handle_frame_select,
        inputs=None,
        outputs=[tb_frame_info_box, *frame_buttons],
    )
    tb_delete_selected_frame_btn.click(
        fn=tb_handle_delete_and_refresh_gallery,
        inputs=[tb_extracted_folders_dropdown, tb_frame_info_box],
        outputs=[
            tb_frames_gallery,
            tb_frame_info_box,
            *frame_buttons,
            tb_message_output,
        ],
    )
    tb_save_selected_frame_btn.click(
        fn=tb_handle_save_selected_frame,
        inputs=[tb_extracted_folders_dropdown, tb_frame_info_box],
        outputs=[tb_message_output, tb_frame_info_box],
    )
    tb_reassemble_frames_btn.click(
        fn=tb_handle_reassemble_frames,
        inputs=[
            tb_extracted_folders_dropdown,
            tb_reassemble_output_fps,
            tb_reassemble_video_name_input,
        ],
        outputs=[tb_processed_video_output, tb_message_output],
    )

    return tb_toolbox_ui_main_container, tb_input_video_component


# --- Main execution block for standalone mode ---

if __name__ == "__main__":
    import argparse

    def launch_standalone():
        """Creates and launches the Gradio interface for the toolbox when run as a script."""

        # 1. Setup and parse command-line arguments, similar to studio.py
        parser = argparse.ArgumentParser(
            description="Run FramePack Toolbox in Standalone Mode"
        )
        parser.add_argument(
            "--share", action="store_true", help="Enable Gradio sharing link"
        )
        parser.add_argument(
            "--server",
            type=str,
            default="127.0.0.1",
            help="Server name to launch on (default: 127.0.0.1)",
        )
        parser.add_argument(
            "--port",
            type=int,
            required=False,
            help="Server port to launch on (default: 7860)",
        )
        parser.add_argument(
            "--inbrowser", action="store_true", help="Automatically open in browser"
        )
        args = parser.parse_args()

        # 2. The app's stylesheet
        with open(os.path.join(script_dir, "ui", "styles.css"), encoding="utf-8") as f:
            css = f.read()

        # 3. Get the output directory path from the existing settings instance
        output_dir_from_settings = settings_instance.get("output_dir")
        allowed_paths = [output_dir_from_settings]
        logger.info(
            f"Gradio server will be allowed to access path: {output_dir_from_settings}"
        )

        # 4. Create the Gradio interface
        with gr.Blocks(title="FramePack Toolbox (Standalone)", css=css) as block:
            gr.Markdown("## FramePack Tools")

            tb_create_video_toolbox_ui()
        logger.info(
            f"Launching Toolbox server. Access it at http://{args.server}:{args.port if args.port else 7860}"
        )
        block.launch(
            server_name=args.server,
            # 5. Launch the Gradio app with all the configured arguments
            server_port=args.port,
            share=args.share,
            inbrowser=args.inbrowser,
            allowed_paths=allowed_paths,
        )

    # Call the launch function
    launch_standalone()
