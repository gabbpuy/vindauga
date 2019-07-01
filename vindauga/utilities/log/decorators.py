# -*- coding: utf-8 -*-
from functools import wraps

depth = 0


def log(logger):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            fName = fn.__name__
            global depth
            indent = '.' * depth
            depth += 1
            logger.info("%s%s(%s, %s) IN", indent, fName, args, kwargs)
            try:
                results = fn(*args, **kwargs)
                try:
                    logger.debug("%s%s returns %s", indent, fName, results)
                except TypeError:
                    logger.debug("%s%s returns %s", indent, fName, str(results))
                return results
            except Exception as e:
                logger.exception("%s%s raised %s", indent, fName, e)
                raise
            finally:
                depth -= 1
                indent = '.' * depth
                logger.info("%s%s OUT", indent, fName)

        return wrapper
    return decorator
