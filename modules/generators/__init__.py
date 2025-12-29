from .original_generator import OriginalModelGenerator
from .f1_generator import F1ModelGenerator
from .video_generator import VideoModelGenerator
from .video_f1_generator import VideoF1ModelGenerator
from .original_with_endframe_generator import OriginalWithEndframeModelGenerator

def create_model_generator(model_type, **kwargs):
    """
    Create a model generator based on the model type.
    
    Args:
        model_type: The type of model to create ("Original", "Original with Endframe", "F1", "Video", or "Video F1")
        **kwargs: Additional arguments to pass to the model generator constructor
        
    Returns:
        A model generator instance
        
    Raises:
        ValueError: If the model type is not supported
    """
    if model_type == "Original":
        return OriginalModelGenerator(**kwargs)
    elif model_type == "Original with Endframe":
        return OriginalWithEndframeModelGenerator(**kwargs)
    elif model_type == "F1":
        return F1ModelGenerator(**kwargs)
    elif model_type == "Video":
        return VideoModelGenerator(**kwargs)
    elif model_type == "Video F1":
        return VideoF1ModelGenerator(**kwargs)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
