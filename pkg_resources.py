class DistributionNotFound(Exception):
    """Stub exception for environments lacking setuptools."""
    pass


def get_distribution(dist_name):
    """Return a minimal stub distribution with a version attribute."""
    class Distribution:
        version = "0"
    return Distribution()
