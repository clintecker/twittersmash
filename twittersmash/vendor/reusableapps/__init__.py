try:
    from pkg_resources import working_set, DistributionNotFound, Environment, \
        VersionConflict, UnknownExtra
except ImportError:
    Environment = None

REUSEABLE_APPS = []

class ReusableAppsError(Exception):
    pass

def search(apps_paths=None, installed_apps=None):
    """
    Searches in the given apps directories for Django apps with the entry point
    ``'django.apps'`` and adds them to the python path, if necesary. 
    
    Returns a tuple with all installed and reusable applications.
    """
    if Environment is not None and apps_paths is not None:
        # find every "distributions" in the given paths for reusable apps and
        # add them to the "working_set", effectively setting PYTHONPATH
        distributions, errors = working_set.find_plugins(Environment(apps_paths))
        for dist in distributions:
            working_set.add(dist)
        for dist, e in errors.iteritems():
            if isinstance(e, DistributionNotFound):
                raise ReusableAppsError('"%s": ("%s" not found)', dist, e)
            elif isinstance(e, VersionConflict):
                raise ReusableAppsError('"%s": (version conflict "%s")', dist, e)
            elif isinstance(e, UnknownExtra):
                raise ReusableAppsError('"%s": (unknown extra "%s")', dist, e)
            elif isinstance(e, ImportError):
                raise ReusableAppsError('"%s": (can\'t import "%s")', dist, e)
            else:
                raise ReusableAppsError('"%s": (error "%s")', dist, e)

        # look for entry points in all distributions of the current working set
        # (on the PYTHONPATH) and add matching modules to INSTALLED_APPS
        for entry in working_set.iter_entry_points('django.apps'):
            app_name = entry.module_name
            if app_name not in installed_apps and app_name not in REUSEABLE_APPS:
                REUSEABLE_APPS.append(entry.module_name)
        return installed_apps + tuple(REUSEABLE_APPS)
