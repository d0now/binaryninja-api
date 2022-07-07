
import ctypes
import inspect
from typing import Generator, Optional, List, Tuple, Union, Mapping, Any, Dict
from dataclasses import dataclass

from . import binaryview

from . import function
from . import _binaryninjacore as core
from binaryninja.types import Type



class Component:
    def __init__(self, view=None, handle=None):

        self.view: 'BinaryView' = view

        if not handle:
            self.handle = core.BNComponentCreateEmpty()
        else:
            self.handle = handle

        self.guid = core.BNComponentGetGUID(self.handle)

    def __eq__(self, other):
        if not isinstance(other, Component):
            return NotImplemented
        return core.BNComponentsEqual(self.handle, other.handle)

    def __repr__(self):
        return f'<Component "{self.guid[:8]}...">'

    def __del__(self):
        core.BNFreeComponent(self.handle)

    def add_function(self, func: function.Function) -> bool:
        return core.BNComponentAddFunctionReference(self.handle, func.handle, True)

    def contains_function(self, func: function.Function) -> bool:
        return core.BNComponentContainsFunction(self.handle, func.handle)

    def remove_function(self, func: function.Function) -> bool:
        return core.BNComponentRemoveFunctionReference(self.handle, func.handle, True)

    def add_component(self, component: 'Component') -> bool:
        return core.BNComponentAddComponentReference(self.handle, component.handle)

    def contains_component(self, component: 'Component') -> bool:
        return core.BNComponentContainsComponent(self.handle, component.handle)

    def remove_component(self, component: 'Component') -> bool:
        return core.BNComponentRemoveComponentReference(self.handle, component.handle)

    @property
    def name(self):
        return core.BNComponentGetName(self.handle)

    @name.setter
    def name(self, _name):
        core.BNComponentSetName(self.handle, _name)

    @property
    def parent(self):
        bn_component = core.BNComponentGetParent(self.handle)
        if bn_component is not None:
            return Component(self.view, core.BNComponentGetParent(self.handle))
        return None

    @property
    def components(self) -> List['Component']:
        components = []
        count = ctypes.c_ulonglong(0)
        bn_components = core.BNComponentGetContainedComponents(self.handle, count)

        for i in range(count.value):
            components.append(Component(self.view, bn_components[i]))

        return components

    @property
    def functions(self) -> List[function.Function]:
        functions = []
        count = ctypes.c_ulonglong(0)
        bn_functions = core.BNComponentGetContainedFunctions(self.handle, count)

        for i in range(count.value):
            bn_component = bn_functions[i]
            component = function.Function(self.view, bn_component)
            functions.append(component)

        return functions

    def get_referenced_data_variables(self, recursive=False):
        data_vars = []
        count = ctypes.c_ulonglong(0)
        if recursive:
            bn_data_vars = core.BNComponentGetReferencedDataVariablesRecursive(self.handle, count)
        else:
            bn_data_vars = core.BNComponentGetReferencedDataVariables(self.handle, count)
        try:
            for i in range(count.value):
                bn_data_var = bn_data_vars[i]
                data_var = binaryview.DataVariable.from_core_struct(bn_data_var, self.view)
                data_vars.append(data_var)
        finally:
            core.BNFreeDataVariables(bn_data_vars, count.value)
        return data_vars

    def get_referenced_types(self, recursive=False):
        types = []
        count = ctypes.c_ulonglong(0)

        bn_types = core.BNComponentGetReferencedTypes(self.handle, count)

        for i in range(count.value):
            types.append(Type(bn_types[i]))

        return types
