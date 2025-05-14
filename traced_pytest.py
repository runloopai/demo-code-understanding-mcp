#!/usr/bin/env python3
import sys
import os
import inspect
import site
import argparse
from collections import defaultdict

def safe_repr(value):
    """
    Safe repr for values that may not be reprable.
    """
    try:
        return repr(value)
    except Exception:
        return f"<{type(value).__name__}>"

class CallTreeTracer:
    def __init__(self, project_root, trace_packages=None):
        self.project_root = os.path.realpath(project_root)
        self.trace_packages = trace_packages or []
        # build a set of paths to ignore (venv, stdlib, site-packages)
        self.ignore_dirs = {
            os.path.realpath(sys.prefix),
            os.path.realpath(sys.exec_prefix),
        }
        for p in site.getsitepackages() + [site.getusersitepackages()]:
            self.ignore_dirs.add(os.path.realpath(p))

        self.trees = defaultdict(list)    # test_id → list of (depth, func, args, relpath, lineno)
        self.current_test = None
        self.depth = 0
        self.is_in_trace_package = False

    def _is_trace_package_file(self, fpath):
        # check if file is in a tracked package
        if self.trace_packages:
            for package in self.trace_packages:
                if package in fpath:
                    return True
        return False

    def _should_trace_file(self, filename, event):
        # only real .py files under project_root, not in any ignore_dirs
        fpath = os.path.realpath(filename)
        
        if self._is_trace_package_file(fpath):
            if self.is_in_trace_package:
                return False
            # upon entering a trace package, we should ignore tracing until we return to the main project
            self.is_in_trace_package = True
            return True

        if not fpath.startswith(self.project_root + os.sep):
            return False
        if not fpath.endswith('.py'):
            return False
        if not os.path.isfile(fpath):
            return False
        for ign in self.ignore_dirs:
            if fpath.startswith(ign + os.sep):
                return False
        if '__pycache__' in fpath:
            return False       

        # We are back at a boundary of our own project, reset the tracing state
        if event == 'return' and self.is_in_trace_package:
            self.is_in_trace_package = False
            self.depth = max(self.depth - 1, 0)
        return True

    def trace(self, frame, event, arg):
        code = frame.f_code
        fname = code.co_name
        fpath = code.co_filename

        # detect entry into a test function
        if event == 'call' and fname.startswith('test_') and self._should_trace_file(fpath, event):
            module = frame.f_globals.get('__name__', '<unknown>')
            self.current_test = f"{module}.{fname}"
            # indent first child calls
            self.depth = 1
            return self.trace

        # if not in a test, do nothing
        if not self.current_test:
            return self.trace

        # only trace calls from real project files
        if not self._should_trace_file(fpath, event):
            return self.trace

        if event == 'call':
            info = inspect.getargvalues(frame)
            # capture args, varargs, kwargs
            args = {name: info.locals.get(name) for name in info.args}
            if info.varargs:
                args['*' + info.varargs] = info.locals.get(info.varargs)
            if info.keywords:
                args['**' + info.keywords] = info.locals.get(info.keywords)

            rel = os.path.relpath(fpath, self.project_root)
            self.trees[self.current_test].append(
                (self.depth, fname, args, rel, frame.f_lineno)
            )
            self.depth += 1

        elif event == 'return':
            # if returning from the test itself, end tracing
            if self.current_test.split('.')[-1] == fname:
                self.current_test = None
                self.depth = 0
            else:
                self.depth = max(self.depth - 1, 0)

        return self.trace

    def report(self):     
        for test_id, calls in self.trees.items():
            print(f"\nCall tree for {test_id}:")
            for depth, func, args, rel, lineno in calls:
                indent = ' ' * (depth * 2)
                args_str = ', '.join(f"{k}={safe_repr(v)}" for k, v in args.items())
                print(f"{indent}{func}({args_str})  [{rel}:{lineno}]")

def main():
    parser = argparse.ArgumentParser(description='Run pytest with function call tracing')
    parser.add_argument('--trace-package', action='append', help='Additional package to trace (can be specified multiple times)')
    args, remaining = parser.parse_known_args()

    project_root = os.getcwd()
    tracer = CallTreeTracer(project_root, trace_packages=args.trace_package)

    # install tracer before pytest loads
    sys.settrace(tracer.trace)

    import pytest
    exit_code = pytest.main(remaining)

    # stop tracing & dump trees
    sys.settrace(None)
    tracer.report()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()