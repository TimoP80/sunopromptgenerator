import warnings

# Suppress the specific DeprecationWarning from torch.distributed._shard.checkpoint
warnings.filterwarnings(
    "ignore",
    message="`torch.distributed._shard.checkpoint` will be deprecated, use `torch.distributed.checkpoint` instead",
    category=DeprecationWarning
)