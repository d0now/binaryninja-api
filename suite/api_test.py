import unittest
import os

import binaryninja as bn
from binaryninja.binaryview import BinaryView, BinaryViewType
from binaryninja.settings import Settings, SettingsScope
from binaryninja.metadata import Metadata
from binaryninja.demangle import demangle_gnu3, demangle_ms, get_qualified_name
from binaryninja.architecture import Architecture
from binaryninja.pluginmanager import RepositoryManager
from binaryninja.platform import Platform
from binaryninja.enums import (
    StructureVariant, NamedTypeReferenceClass, MemberAccess, MemberScope, ReferenceType, VariableSourceType,
    SymbolBinding, SymbolType, TokenEscapingType, InstructionTextTokenType, TypeDefinitionLineType
)

from binaryninja.types import (
	QualifiedName, Type, TypeBuilder, EnumerationMember, FunctionParameter, OffsetWithConfidence, BoolWithConfidence,
	EnumerationBuilder, NamedTypeReferenceBuilder, StructureBuilder, StructureMember, IntegerType, StructureType,
	Symbol, NameSpace, MutableTypeBuilder, NamedTypeReferenceType, QualifiedNameType, TypeDefinitionLine
)
from binaryninja.function import *
from binaryninja.basicblock import *
from binaryninja.binaryview import *
from binaryninja.lowlevelil import *
from binaryninja.mediumlevelil import *
from binaryninja.highlevelil import *
from binaryninja.variable import *
from binaryninja.typeparser import *
from binaryninja.typeprinter import *
import zipfile


class FileApparatus:
	test_store = "binaries/test_corpus"

	def __init__(self, filename):
		self.filename = filename
		if not os.path.exists(self.path):
			with zipfile.ZipFile(self.path + ".zip", "r") as zf:
				zf.extractall(path=os.path.dirname(__file__))
		assert os.path.exists(self.path)

	@property
	def path(self) -> str:
		return os.path.join(os.path.dirname(__file__), self.test_store, self.filename)

	def __del__(self):
		if os.path.exists(self.path):
			os.unlink(self.path)

	def __enter__(self):
		return self.path

	def __exit__(self, type, value, traceback):
		pass

class Apparatus:
	def __init__(self, filename):
		with FileApparatus(filename) as path:
			self.bv = BinaryViewType.get_view_of_file(os.path.relpath(path))

	def __del__(self):
		self.bv.file.close()

	def __enter__(self):
		return self.bv

	def __exit__(self, type, value, traceback):
		pass


class TestWithBinaryView(unittest.TestCase):
	file_name = "helloworld"

	def setUp(self):
		self.apparatus = Apparatus(self.file_name)
		self.bv = self.apparatus.bv
		self.arch = self.bv.arch
		self.plat = self.bv.platform


class SettingsAPI(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		pass

	@classmethod
	def tearDownClass(cls):
		pass

	def test_settings_create(self):
		s1 = Settings()
		s2 = Settings(None)
		s3 = Settings("default")
		s4 = Settings("test")
		assert s1 == s2, "test_settings_create failed"
		assert s1 == s3, "test_settings_create failed"
		assert s1 != s4, "test_settings_create failed"

	def test_settings_defaults(self):
		settings = Settings()
		assert settings.contains("analysis.linearSweep.autorun"), "test_settings_defaults failed"
		assert settings.contains("analysis.unicode.blocks"), "test_settings_defaults failed"
		assert settings.contains("network.downloadProviderName"), "test_settings_defaults failed"
		assert settings.get_bool_with_scope("analysis.linearSweep.autorun", scope=SettingsScope.SettingsDefaultScope
		                                    )[0], "test_settings_defaults failed"
		assert settings.get_bool_with_scope("analysis.linearSweep.autorun", scope=SettingsScope.SettingsDefaultScope
		                                    )[1] == SettingsScope.SettingsDefaultScope, "test_settings_defaults failed"

	def test_settings_registration(self):
		settings = Settings("test")
		assert not settings.contains("testGroup.testSetting"), "test_settings_registration failed"
		assert settings.register_group("testGroup", "Title"), "test_settings_registration failed"
		assert settings.register_setting(
		    "testGroup.testSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : true, "type" : "boolean", "id" : "testSetting"}'
		), "test_settings_registration failed"
		assert settings.contains("testGroup.testSetting"), "test_settings_registration failed"

	def test_settings_usage(self):
		settings = Settings("test")
		assert not settings.contains("testGroup.testSetting"), "test_settings_types failed"
		assert settings.register_group("testGroup", "Title"), "test_settings_types failed"
		assert not settings.register_setting(
		    "testGroup.boolSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : 500, "type" : "boolean", "id" : "boolSetting"}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.boolSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : true, "type" : "boolean", "id" : "boolSetting"}'
		), "test_settings_types failed"
		assert not settings.register_setting(
		    "testGroup.doubleSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : true, "type" : "number", "id" : "doubleSetting"}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.doubleSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : 500, "type" : "number", "id" : "doubleSetting"}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.integerSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : 500, "type" : "number", "id" : "integerSetting"}'
		), "test_settings_types failed"
		assert not settings.register_setting(
		    "testGroup.stringSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : 500, "type" : "string", "id" : "stringSetting"}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.stringSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : "value", "type" : "string", "id" : "stringSetting"}'
		), "test_settings_types failed"
		assert not settings.register_setting(
		    "testGroup.stringListSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : true, "type" : "array", "elementType" : "string", "id" : "stringListSetting"}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.stringListSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : ["value1", "value2"], "type" : "array", "elementType" : "string", "id" : "stringListSetting"}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.ignoreResourceBoolSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : true, "type" : "boolean", "id" : "boolSetting", "ignore" : ["SettingsResourceScope"]}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.ignoreUserBoolSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : true, "type" : "boolean", "id" : "boolSetting", "ignore" : ["SettingsUserScope"]}'
		), "test_settings_types failed"
		assert settings.register_setting(
		    "testGroup.readOnlyBoolSetting",
		    '{"description" : "Test description.", "title" : "Test Title", "default" : true, "type" : "boolean", "id" : "boolSetting", "ignore" : ["SettingsResourceScope", "SettingsUserScope"]}'
		), "test_settings_types failed"

		assert settings.contains("testGroup.boolSetting"), "test_settings_types failed"
		assert settings.contains("testGroup.doubleSetting"), "test_settings_types failed"
		assert settings.contains("testGroup.integerSetting"), "test_settings_types failed"
		assert settings.contains("testGroup.stringSetting"), "test_settings_types failed"
		assert settings.contains("testGroup.stringListSetting"), "test_settings_types failed"

		assert settings.get_bool("testGroup.boolSetting") == True, "test_settings_types failed"
		assert settings.get_double("testGroup.doubleSetting") == 500, "test_settings_types failed"
		assert settings.get_integer("testGroup.integerSetting") == 500, "test_settings_types failed"
		assert settings.get_string("testGroup.stringSetting") == "value", "test_settings_types failed"
		assert settings.get_string_list("testGroup.stringListSetting") == [
		    "value1", "value2"
		], "test_settings_types failed"

		assert settings.set_bool("testGroup.boolSetting", False), "test_settings_types failed"
		assert settings.set_double("testGroup.doubleSetting", 700), "test_settings_types failed"
		assert settings.set_integer("testGroup.integerSetting", 700), "test_settings_types failed"
		assert settings.set_string("testGroup.stringSetting", "value_user"), "test_settings_types failed"
		assert settings.set_string_list(
		    "testGroup.stringListSetting", ["value3", "value4"]
		), "test_settings_types failed"

		assert settings.get_bool("testGroup.boolSetting") == False, "test_settings_types failed"
		assert settings.get_double("testGroup.doubleSetting") == 700, "test_settings_types failed"
		assert settings.get_integer("testGroup.integerSetting") == 700, "test_settings_types failed"
		assert settings.get_string("testGroup.stringSetting") == "value_user", "test_settings_types failed"
		assert settings.get_string_list("testGroup.stringListSetting") == [
		    "value3", "value4"
		], "test_settings_types failed"

		assert settings.get_bool_with_scope("testGroup.boolSetting", scope=SettingsScope.SettingsDefaultScope
		                                    )[0] == True, "test_settings_types failed"
		assert settings.get_double_with_scope("testGroup.doubleSetting", scope=SettingsScope.SettingsDefaultScope
		                                      )[0] == 500, "test_settings_types failed"
		assert settings.get_integer_with_scope("testGroup.integerSetting", scope=SettingsScope.SettingsDefaultScope
		                                       )[0] == 500, "test_settings_types failed"
		assert settings.get_string_with_scope("testGroup.stringSetting", scope=SettingsScope.SettingsDefaultScope
		                                      )[0] == "value", "test_settings_types failed"
		assert settings.get_string_list_with_scope(
		    "testGroup.stringListSetting", scope=SettingsScope.SettingsDefaultScope
		)[0] == ["value1", "value2"], "test_settings_types failed"

		assert settings.get_bool_with_scope("testGroup.boolSetting", scope=SettingsScope.SettingsUserScope
		                                    )[0] == False, "test_settings_types failed"
		assert settings.get_double_with_scope("testGroup.doubleSetting", scope=SettingsScope.SettingsUserScope
		                                      )[0] == 700, "test_settings_types failed"
		assert settings.get_integer_with_scope("testGroup.integerSetting", scope=SettingsScope.SettingsUserScope
		                                       )[0] == 700, "test_settings_types failed"
		assert settings.get_string_with_scope("testGroup.stringSetting", scope=SettingsScope.SettingsUserScope
		                                      )[0] == "value_user", "test_settings_types failed"
		assert settings.get_string_list_with_scope(
		    "testGroup.stringListSetting", scope=SettingsScope.SettingsUserScope
		)[0] == ["value3", "value4"], "test_settings_types failed"

		raw_view = BinaryView.new(b'0x55')
		assert not settings.set_bool(
		    "testGroup.ignoreResourceBoolSetting", False, scope=SettingsScope.SettingsDefaultScope
		), "test_settings_types failed"
		assert not settings.set_bool(
		    "testGroup.ignoreResourceBoolSetting", False, scope=SettingsScope.SettingsResourceScope
		), "test_settings_types failed"
		assert not settings.set_bool(
		    "testGroup.ignoreResourceBoolSetting", False, raw_view, scope=SettingsScope.SettingsResourceScope
		), "test_settings_types failed"
		assert settings.set_bool(
		    "testGroup.ignoreResourceBoolSetting", False, scope=SettingsScope.SettingsUserScope
		), "test_settings_types failed"
		assert not settings.set_bool("testGroup.ignoreUserBoolSetting", False), "test_settings_types failed"
		assert settings.set_bool("testGroup.ignoreUserBoolSetting", False, raw_view), "test_settings_types failed"
		assert settings.set_bool(
		    "testGroup.ignoreUserBoolSetting", False, raw_view, scope=SettingsScope.SettingsResourceScope
		), "test_settings_types failed"
		assert not settings.set_bool("testGroup.readOnlyBoolSetting", False), "test_settings_types failed"
		assert not settings.set_bool(
		    "testGroup.readOnlyBoolSetting", False, scope=SettingsScope.SettingsResourceScope
		), "test_settings_types failed"
		assert not settings.set_bool(
		    "testGroup.readOnlyBoolSetting", False, scope=SettingsScope.SettingsUserScope
		), "test_settings_types failed"

		s2 = Settings("test2")
		assert s2.serialize_schema() == "", "test_settings_types failed"
		test_schema = settings.serialize_schema()
		assert test_schema != "", "test_settings_types failed"
		assert s2.deserialize_schema(test_schema), "test_settings_types failed"

		assert s2.get_bool("testGroup.boolSetting") == True, "test_settings_types failed"
		assert s2.get_double("testGroup.doubleSetting") == 500, "test_settings_types failed"
		assert s2.get_integer("testGroup.integerSetting") == 500, "test_settings_types failed"
		assert s2.get_string("testGroup.stringSetting") == "value", "test_settings_types failed"
		assert s2.get_string_list("testGroup.stringListSetting") == ["value1", "value2"], "test_settings_types failed"

		assert s2.deserialize_settings(
		    settings.serialize_settings(scope=SettingsScope.SettingsUserScope), raw_view,
		    SettingsScope.SettingsResourceScope
		), "test_settings_types failed"
		assert s2.get_bool("testGroup.boolSetting", raw_view) == False, "test_settings_types failed"
		assert s2.get_double("testGroup.doubleSetting", raw_view) == 700, "test_settings_types failed"
		assert s2.get_integer("testGroup.integerSetting", raw_view) == 700, "test_settings_types failed"
		assert s2.get_string("testGroup.stringSetting", raw_view) == "value_user", "test_settings_types failed"
		assert s2.get_string_list("testGroup.stringListSetting",
		                          raw_view) == ["value3", "value4"], "test_settings_types failed"

		assert s2.reset_all(), "test_settings_types failed"
		assert s2.get_bool("testGroup.boolSetting") == True, "test_settings_types failed"
		assert s2.get_double("testGroup.doubleSetting") == 500, "test_settings_types failed"
		assert s2.get_integer("testGroup.integerSetting") == 500, "test_settings_types failed"
		assert s2.get_string("testGroup.stringSetting") == "value", "test_settings_types failed"
		assert s2.get_string_list("testGroup.stringListSetting") == ["value1", "value2"], "test_settings_types failed"

		s3 = Settings("test3")
		assert s3.deserialize_schema(test_schema, SettingsScope.SettingsResourceScope)
		assert not s3.contains("testGroup.ignoreResourceBoolSetting"), "test_settings_types failed"
		assert s3.contains("testGroup.ignoreUserBoolSetting"), "test_settings_types failed"
		assert not s3.contains("testGroup.readOnlyBoolSetting"), "test_settings_types failed"

		assert s3.deserialize_schema(test_schema, SettingsScope.SettingsUserScope, False)
		assert s3.contains("testGroup.ignoreResourceBoolSetting"), "test_settings_types failed"
		assert not s3.contains("testGroup.ignoreUserBoolSetting"), "test_settings_types failed"
		assert not s3.contains("testGroup.readOnlyBoolSetting"), "test_settings_types failed"

		assert s3.deserialize_schema(test_schema, SettingsScope.SettingsUserScope, False)
		assert s3.deserialize_schema(s3.serialize_schema(), SettingsScope.SettingsResourceScope, False)
		assert not s3.contains("testGroup.ignoreResourceBoolSetting"), "test_settings_types failed"
		assert not s3.contains("testGroup.ignoreUserBoolSetting"), "test_settings_types failed"
		assert not s3.contains("testGroup.readOnlyBoolSetting"), "test_settings_types failed"

	def test_load_settings(self):
		bvt_name = "Mapped (Python)" if "Mapped (Python)" in map(
		    lambda bvt: bvt.name, list(BinaryViewType)
		) else "Mapped"
		raw_view = BinaryView.new(b'0x55')
		assert raw_view.view_type == "Raw", "test_load_settings failed"
		mapped_view = BinaryViewType[bvt_name].create(raw_view)
		assert mapped_view.view_type == bvt_name, "test_load_settings failed"
		assert mapped_view.segments[0].start == 0, "test_load_settings failed"
		assert len(mapped_view) == 4, "test_load_settings failed"
		load_settings = BinaryViewType[bvt_name].get_load_settings_for_data(raw_view)
		assert load_settings is not None, "test_load_settings failed"
		assert load_settings.contains("loader.architecture"), "test_load_settings failed"
		assert load_settings.contains("loader.platform"), "test_load_settings failed"
		assert load_settings.contains("loader.imageBase"), "test_load_settings failed"
		assert load_settings.contains("loader.entryPointOffset"), "test_load_settings failed"
		load_settings.set_string("loader.architecture", 'x86_64')
		load_settings.set_integer("loader.imageBase", 0x500000)
		load_settings.set_integer("loader.entryPointOffset", 0)
		raw_view.set_load_settings(bvt_name, load_settings)
		mapped_view = BinaryViewType[bvt_name].create(raw_view)
		assert mapped_view.view_type == bvt_name, "test_load_settings failed"
		assert mapped_view.segments[0].start == 0x500000, "test_load_settings failed"
		assert len(mapped_view) == 4, "test_load_settings failed"
		assert raw_view.get_load_settings(bvt_name) == load_settings
		raw_view.set_load_settings(bvt_name, None)
		assert raw_view.get_load_settings(bvt_name) is None


class MetaddataAPI(TestWithBinaryView):
	def test_metadata_basic_types(self):
		# Core is tested thoroughly through the C++ unit tests here we focus on the python api side
		md = Metadata(1)
		assert md.is_integer
		assert int(md) == 1
		assert md.value == 1

		md = Metadata(-1, signed=True)
		assert md.is_signed_integer
		assert int(md) == -1
		assert md.value == -1
		md = Metadata(1, signed=False)
		assert md.is_unsigned_integer
		assert int(md) == 1
		md = Metadata(3.14)
		assert md.is_float
		assert float(md) == 3.14
		assert md.value == 3.14

		md = Metadata("asdf")
		assert md.is_string
		assert str(md) == "asdf"
		assert len(md) == 4
		assert md.value == "asdf"

		md = Metadata(b"\x00\x00\x41\x00")
		assert len(md) == 4
		assert bytes(md) == b"\x00\x00\x41\x00"

	def test_metadata_compound_types(self):
		md = Metadata([1, 2, 3])
		assert md.is_array
		assert md.value == [1, 2, 3]
		assert len(md) == 3
		assert md[0] == 1
		assert md[1] == 2
		assert md[2] == 3
		assert isinstance(list(md), list)
		md.remove(0)
		assert len(md) == 2
		assert md == [2, 3]

		md = Metadata({"a": 1, "b": 2})
		assert md.is_dict
		assert len(md) == 2
		assert md.value == {"a": 1, "b": 2}
		assert md["a"] == 1
		assert md["b"] == 2
		md.remove("a")
		assert len(md) == 1
		assert md == {"b": 2}

	def test_metadata_equality(self):
		assert Metadata(1) == 1
		assert Metadata(1) != 0
		assert Metadata(1) == Metadata(1)
		assert Metadata(1) != Metadata(0)

		assert Metadata(3.14) == 3.14
		assert Metadata(3.14) == Metadata(3.14)
		assert Metadata(3.14) != 3.1
		assert Metadata(3.14) != Metadata(3.1)

		assert Metadata("asdf") == "asdf"
		assert Metadata("asdf") == Metadata("asdf")
		assert Metadata("asdf") != "qwer"
		assert Metadata("asdf") != Metadata("qwer")

		assert Metadata(b"as\x00df") == b"as\x00df"
		assert Metadata(b"as\x00df") == Metadata(b"as\x00df")
		assert Metadata(b"as\x00df") != b"qw\x00er"
		assert Metadata(b"as\x00df") != Metadata(b"qw\x00er")

		assert Metadata([1, 2, 3]) == [1, 2, 3]
		assert Metadata([1, 2, 3]) == Metadata([1, 2, 3])
		assert Metadata([1, 2, 3]) != [1, 2]
		assert Metadata([1, 2, 3]) != Metadata([1, 2])

		assert Metadata({"a": 1, "b": 2}) == {"a": 1, "b": 2}
		assert Metadata({"a": 1, "b": 2}) == Metadata({"a": 1, "b": 2})
		assert Metadata({"a": 1, "b": 2}) != {"a": 1}
		assert Metadata({"a": 1, "b": 2}) != Metadata({"a": 1})

	def test_binaryview_storage(self):
		data = b"some bytes\x00\xff\xff\xff\xfe\xff\xcd\xcc"
		self.bv.store_metadata("SomeKey", data)
		assert self.bv.query_metadata("SomeKey") == data
		assert bytes(self.bv.query_metadata("SomeKey")) == data

class DemanglerTest(unittest.TestCase):
	def get_type_string(self, t, n):
		out = ""
		if t is not None:
			out = str(t.get_string_before_name())
			if len(out) > 1 and out[-1] != ' ':
				out += " "
			out += get_qualified_name(n)
			out += str(t.get_string_after_name())
		return out

	def test_demangle_ms(self):
		tests = ("??_V@YAPAXI@Z", "??_U@YAPAXI@Z")

		oracle = ("void* __cdecl operator delete[](uint32_t)", "void* __cdecl operator new[](uint32_t)")
		for i, test in enumerate(tests):
			t, n = demangle_ms(Architecture['x86'], test)
			result = self.get_type_string(t, n)
			assert result == oracle[i], f"oracle: {oracle[i]}\nresult: {result}"

	def test_demangle_gnu3(self):
		tests = (
		    "__ZN15BinaryNinjaCore12BinaryReader5Read8Ev", "__ZN5QListIP18QAbstractAnimationE18detach_helper_growEii",
		    "__ZN13QStatePrivate22emitPropertiesAssignedEv",
		    "__ZN17QtMetaTypePrivate23QMetaTypeFunctionHelperI14QItemSelectionLb1EE9ConstructEPvPKv",
		    "__ZN18QSharedDataPointerI16QFileInfoPrivateE4dataEv", "__ZN26QAbstractNativeEventFilterD2Ev",
		    "__ZN5QListIP14QAbstractStateE3endEv",
		    "__ZNK15BinaryNinjaCore19ArchitectureWrapper22GetOpcodeDisplayLengthEv",
		    "__ZN15BinaryNinjaCore17ScriptingInstance19SetCurrentSelectionEyy",
		    "__ZN12_GLOBAL__N_114TypeDestructor14DestructorImplI11QStringListLb1EE8DestructEiPv",
		    "__ZN13QGb18030Codec5_nameEv", "__ZN5QListIP7QObjectE6detachEv",
		    "__ZN19QBasicAtomicPointerI9QFreeListI13QMutexPrivateN12_GLOBAL__N_117FreeListConstantsEEE17testAndSetReleaseEPS4_S6_",
		    "__ZN12QJsonPrivate6Parser12reserveSpaceEi", "__ZN20QStateMachinePrivate12endMacrostepEb",
		    "__ZN14QScopedPointerI20QTemporaryDirPrivate21QScopedPointerDeleterIS0_EED2Ev",
		    "__ZN14QVariantIsNullIN12_GLOBAL__N_115CoreTypesFilterEE8delegateI10QMatrix4x4EEbPKT_",
		    "__ZN26QAbstractProxyModelPrivateC2Ev",
		    "__ZNSt3__110__function6__funcIZ26BNWorkerInteractiveEnqueueE4$_16NS_9allocatorIS2_EEFvvEEclEv"
		)

		oracle = (
		    "int32_t BinaryNinjaCore::BinaryReader::Read8()",
		    "int32_t QList<QAbstractAnimation*>::detach_helper_grow(int32_t, int32_t)",
		    "int32_t QStatePrivate::emitPropertiesAssigned()",
		    "int32_t QtMetaTypePrivate::QMetaTypeFunctionHelper<QItemSelection, true>::Construct(void*, void const*)",
		    "int32_t QSharedDataPointer<QFileInfoPrivate>::data()",
		    "void QAbstractNativeEventFilter::~QAbstractNativeEventFilter()", "int32_t QList<QAbstractState*>::end()",
		    "int32_t BinaryNinjaCore::ArchitectureWrapper::GetOpcodeDisplayLength() const",
		    "int32_t BinaryNinjaCore::ScriptingInstance::SetCurrentSelection(uint64_t, uint64_t)",
		    "int32_t (anonymous namespace)::TypeDestructor::DestructorImpl<QStringList, true>::Destruct(int32_t, void*)",
		    "int32_t QGb18030Codec::_name()", "int32_t QList<QObject*>::detach()",
		    "int32_t QBasicAtomicPointer<QFreeList<QMutexPrivate, (anonymous namespace)::FreeListConstants> >::testAndSetRelease(QFreeList<QMutexPrivate, (anonymous namespace)::FreeListConstants>*, QFreeList<QMutexPrivate, (anonymous namespace)::FreeListConstants>*)",
		    "int32_t QJsonPrivate::Parser::reserveSpace(int32_t)", "int32_t QStateMachinePrivate::endMacrostep(bool)",
		    "void QScopedPointer<QTemporaryDirPrivate, QScopedPointerDeleter<QTemporaryDirPrivate> >::~QScopedPointer()",
		    "bool QVariantIsNull<(anonymous namespace)::CoreTypesFilter>::delegate<QMatrix4x4>(QMatrix4x4 const*)",
		    "void QAbstractProxyModelPrivate::QAbstractProxyModelPrivate()",
		    "int32_t std::__1::__function::__func<BNWorkerInteractiveEnqueue::$_16, std::__1::allocator<BNWorkerInteractiveEnqueue::$_16>, void ()>::operator()()"
		)

		for i, test in enumerate(tests):
			t, n = demangle_gnu3(Architecture['x86'], test)
			result = self.get_type_string(t, n)
			assert result == oracle[i], f"oracle: '{oracle[i]}'\nresult: '{result}'"


class PluginManagerTest(unittest.TestCase):
	def test_install_plugin(self):
		mgr = RepositoryManager()
		assert mgr.check_for_updates()
		assert mgr.default_repository.path == 'community'
		assert 'community' in [r.path for r in mgr.repositories]
		assert 'official' in [r.path for r in mgr.repositories]
		assert 'Vector35_Z80' in [p.path for p in mgr['official'].plugins]
		try:
			plugin = mgr['official']['Vector35_Z80']
			assert plugin.dependencies == 'z80dis\n'
			assert plugin.name == 'Z80 Architecture Plugin'
			assert not plugin.installed
			assert not plugin.running
			assert not plugin.enabled
			assert not plugin.disable_pending
			plugin.install()
			plugin.enable()
			assert plugin.installed
			assert plugin.enabled
		finally:
			plugin.uninstall()


class TypeParserTest(unittest.TestCase):
	def setUp(self):
		self.arch = 'x86_64'
		self.p = Platform[self.arch]

	def test_integers(self):
		integers = [("a", "char a;", 1, True), ("b", "unsigned char b;", 1, False), ("c", "signed char c;", 1, True),
		            ("d", "int8_t d;", 1, True), ("e", "uint8_t e;", 1, False), ("f", "short f;", 2, True),
		            ("g", "unsigned short g;", 2, False), ("h", "signed short h;", 2, True),
		            ("i", "short int i;", 2, True), ("j", "unsigned short int j;", 2, False),
		            ("k", "signed short int k;", 2, True), ("l", "uint16_t l;", 2, False), ("m", "int16_t m;", 2, True),
		            ("n", "int n;", 4, True), ("o", "unsigned int o;", 4, False), ("p", "signed int p;", 4, True),
		            ("t", "int32_t t;", 4, True), ("u", "uint32_t u;", 4, False), ("q", "long int q;", 8, True),
		            ("r", "unsigned long int r;", 8, False), ("s", "signed long int s;", 8, True),
		            ("v", "long long v;", 8, True), ("w", "long long int w;", 8, True),
		            ("x", "unsigned long long int x;", 8, False)]

		for name, definition, size, signed in integers:
			with self.subTest():
				result = self.p.parse_types_from_source(definition)
				var = result.variables[name]
				assert len(var) == size, f"Size for type: {definition} != {size} for arch {self.arch}"
				assert signed == var.signed, f"Sign for type: {definition} isn't {'signed' if signed else 'unsigned'}"

	def test_structures(self):
		structures = [("a", "struct a { uint32_t x; uint64_t y; };", 16, 8, 2),
		              ("b", "struct b { uint64_t x; uint64_t y; };", 16, 8, 2),
		              ("c", "struct c { uint64_t x; uint32_t y; };", 16, 8, 2), ]
		for name, definition, size, alignment, members in structures:
			with self.subTest():
				result = self.p.parse_types_from_source(definition)
				s = result.types[name]
				assert len(
				    s
				) == size, f"Structure property: 'size' {size} incorrect for {definition} got {len(s)} instead"
				assert s.alignment == alignment, f"Structure property: 'alignment' {alignment} incorrect for {definition} got {s.alignment} instead"
				assert len(
				    s.members
				) == members, f"Structure property: 'members' {members} incorrect for {definition} got {len(s.members)} instead"

	def test_alignment_packing(self):
		structures = [("a", "struct a { uint64_t a; uint64_t b; uint64_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint64_t a; uint64_t b; uint32_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint64_t a; uint32_t b; uint64_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint64_t a; uint32_t b; uint32_t c; };", 0x10, (0x0, 0x8, 0xc)),
		              ("a", "struct a { uint64_t a; uint64_t b; uint16_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint64_t a; uint32_t b; uint16_t c; };", 0x10, (0x0, 0x8, 0xc)),
		              ("a", "struct a { uint64_t a; uint16_t b; uint64_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint64_t a; uint16_t b; uint32_t c; };", 0x10, (0x0, 0x8, 0xc)),
		              ("a", "struct a { uint64_t a; uint16_t b; uint16_t c; };", 0x10, (0x0, 0x8, 0xa)),
		              ("a", "struct a { uint64_t a; uint64_t b; uint8_t  c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint64_t a; uint32_t b; uint8_t  c; };", 0x10, (0x0, 0x8, 0xc)),
		              ("a", "struct a { uint64_t a; uint16_t b; uint8_t  c; };", 0x10, (0x0, 0x8, 0xa)),
		              ("a", "struct a { uint64_t a; uint8_t  b; uint64_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint64_t a; uint8_t  b; uint32_t c; };", 0x10, (0x0, 0x8, 0xc)),
		              ("a", "struct a { uint64_t a; uint8_t  b; uint16_t c; };", 0x10, (0x0, 0x8, 0xa)),
		              ("a", "struct a { uint64_t a; uint8_t  b; uint8_t  c; };", 0x10, (0x0, 0x8, 0x9)),
		              ("a", "struct a { uint32_t a; uint64_t b; uint64_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint32_t a; uint32_t b; uint64_t c; };", 0x10, (0x0, 0x4, 0x8)),
		              ("a", "struct a { uint32_t a; uint16_t b; uint64_t c; };", 0x10, (0x0, 0x4, 0x8)),
		              ("a", "struct a { uint32_t a; uint8_t  b; uint64_t c; };", 0x10, (0x0, 0x4, 0x8)),
		              ("a", "struct a { uint16_t a; uint64_t b; uint64_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint16_t a; uint32_t b; uint64_t c; };", 0x10, (0x0, 0x4, 0x8)),
		              ("a", "struct a { uint16_t a; uint16_t b; uint64_t c; };", 0x10, (0x0, 0x2, 0x8)),
		              ("a", "struct a { uint16_t a; uint8_t  b; uint64_t c; };", 0x10, (0x0, 0x2, 0x8)),
		              ("a", "struct a { uint8_t  a; uint64_t b; uint64_t c; };", 0x18, (0x0, 0x8, 0x10)),
		              ("a", "struct a { uint8_t  a; uint32_t b; uint64_t c; };", 0x10, (0x0, 0x4, 0x8)),
		              ("a", "struct a { uint8_t  a; uint16_t b; uint64_t c; };", 0x10, (0x0, 0x2, 0x8)),
		              ("a", "struct a { uint8_t  a; uint8_t b;  uint64_t c; };", 0x10, (0x0, 0x1, 0x8)),
		              ("a", "struct a { uint8_t a; struct { uint64_t c; } b; };", 0x10, (0x0, 0x8)),
		              ("a", "struct a { uint8_t a; struct { uint32_t c; } b; };", 0x8, (0x0, 0x4)),
		              ("a", "struct a { uint8_t a; struct { uint16_t c; } b; };", 0x4, (0x0, 0x2)),
		              ("a", "struct a { uint8_t a; struct { uint16_t c; uint16_t d; } b; };", 0x6, (0x0, 0x2)),
		              ("a", "struct a { uint8_t a; struct { uint8_t c; uint16_t d; } b; };", 0x6, (0x0, 0x2)),
		              ("a", "struct a { uint8_t a; struct { uint8_t c; uint8_t d; } b; };", 0x3, (0x0, 0x1)), ]
		for name, definition, size, member_offsets in structures:
			with self.subTest():
				result = self.p.parse_types_from_source(definition)
				s = result.types[name]
				assert len(
				    s
				) == size, f"Structure property: 'size' {size} incorrect for {definition} got {len(s)} instead"
				for expect_offset, member in zip(member_offsets, s.members):
					assert member.offset == expect_offset, f"Structure member property: 'offset' {expect_offset} incorrect for {member.name} in {definition} got {member.offset} instead"

	def test_escaping(self):
		escaped = [('test', 'test', 'test'), ('a0b', 'a0b', 'a0b'), ('a$b', 'a$b', '`a$b`'), ('a_b', 'a_b', 'a_b'),
		           ('a@b', 'a@b', '`a@b`'), ('a!b', 'a!b', '`a!b`'), ('0a', '0a', '`0a`'), ('_a', '_a', '_a'),
		           ('$a', '$a', '`$a`'), ('@a', '@a', '`@a`'), ('!a', '!a', '`!a`'), ('a::b', 'a::b', '`a::b`'),
		           ('a b', 'a b', '`a b`'), ('a`b', 'a`b', '`a\\`b`'), ('a\\b', 'a\\b', '`a\\\\b`'),
		           ('a\\`b', 'a\\`b', '`a\\\\\\`b`'), ('a\\\\`b', 'a\\\\`b', '`a\\\\\\\\\\`b`'), ]
		for source, expect_none, expect_backticks in escaped:
			got_none = QualifiedName.escape(source, TokenEscapingType.NoTokenEscapingType)
			assert got_none == expect_none, f"Escape test of {source} NoTokenEscapingType got {got_none} expected {expect_none}"
			got_backticks = QualifiedName.escape(source, TokenEscapingType.BackticksTokenEscapingType)
			assert got_backticks == expect_backticks, f"Escape test of {source} BackticksTokenEscapingType got {got_backticks} expected {expect_backticks}"

			got_unesc = QualifiedName.unescape(got_backticks, TokenEscapingType.BackticksTokenEscapingType)
			assert got_unesc == source, f"Escape test round trip for {source} got {got_unesc} from {got_backticks}, expected {source}"

	def test_escaped_parsing(self):
		valid = r'''
		typedef uint32_t `type name with space`;
		typedef `type name with space` `another name`;
		enum `space enum`
		{
			`space enum member 1` = 1,
			`space enum member 2` = 2,
		};
		struct `space struct`
		{
			`another name` `first member`;
			`another name`* `second member`;
			`another name` (*`third member`)(`another name` `argument name`);
		};
		'''
		types = self.p.parse_types_from_source(valid)
		assert types.types['type name with space'] == Type.int(4, False)
		assert types.types['another name'].name == QualifiedName(
		    ['type name with space']
		), f"Expected typedef, got {types.types['another name']}"
		assert len(types.types['space enum'].members) == 2
		assert len(types.types['space struct'].members) == 3
		assert types.types['space struct'].members[0].name == 'first member'
		assert types.types['space struct'].members[1].name == 'second member'
		assert types.types['space struct'].members[1].type.target.name == 'another name'
		assert types.types['space struct'].members[2].name == 'third member'
		assert len(types.types['space struct'].members[2].type.target.parameters) == 1
		assert types.types['space struct'].members[2].type.target.parameters[0].name == 'argument name'

	def test_parse_class(self):
		valid = r'''
		class foo;
		class bar
		{
			foo* foo;
		};
		class baz
		{
			class
			{
				bar m_bar;
			} bar;
			struct
			{
				baz* m_baz;
			} baz;
		};
		'''
		types = self.p.parse_types_from_source(valid)
		assert types.types['foo'].type_class == TypeClass.VoidTypeClass
		assert types.types['bar'].type_class == TypeClass.StructureTypeClass
		assert types.types['bar'].type == StructureVariant.ClassStructureType
		assert types.types['baz'].type_class == TypeClass.StructureTypeClass
		assert types.types['baz'].type == StructureVariant.ClassStructureType
		assert types.types['baz'].members[0].type.type_class == TypeClass.StructureTypeClass
		assert types.types['baz'].members[0].type.type == StructureVariant.ClassStructureType
		assert types.types['baz'].members[1].type.type_class == TypeClass.StructureTypeClass
		assert types.types['baz'].members[1].type.type == StructureVariant.StructStructureType

	def test_class_vs_struct(self):
		# Trying to use `class foo` as `struct foo`

		# Clang says (TIL):
		# "Class 'foo' was previously declared as a struct; this is valid, but may result in linker errors under the Microsoft C++ ABI"
		valid = [
			r'''
				class foo
				{
					int a;
				};
				class bar
				{
					struct foo foo;
				};
			''', r'''
				struct foo
				{
					int a;
				};
				struct bar
				{
					class foo foo;
				};
			'''
		]
		for source in valid:
			with self.subTest():
				types = self.p.parse_types_from_source(source)


	def test_parse_empty(self):
		valid = [
			# Forward declarations
			'struct foo;',
			'class foo;',
			'union foo;',
			# Definition with no members
			'struct foo {};',
			'class foo {};',
			'union foo {};',
			'enum foo {};',
			# Inner structure is empty
			'struct foo { struct {} bar; class {} baz; union {} alpha; enum {} bravo; };',
			'class foo { struct {} bar; class {} baz; union {} alpha; enum {} bravo; };',
			'union foo { struct {} bar; class {} baz; union {} alpha; enum {} bravo; };',
		]
		for source in valid:
			with self.subTest():
				types = self.p.parse_types_from_source(source)

		invalid = [
			# Forward declaration of enum is not allowed
			'enum foo;'
		]
		for source in invalid:
			with self.subTest():
				with self.assertRaises(SyntaxError):
					types = self.p.parse_types_from_source(source)

	def test_parse_nested(self):
		source = r'''
		struct foo
		{
			enum : uint32_t
			{
				a = 1,
				b = 2,
				c = 3
			} bar;
			struct
			{
				uint32_t a;
			} baz;
			class
			{
				uint32_t a;
			} alpha;
			union
			{
				uint32_t a;
				uint32_t b;
			} bravo;
		};
		'''
		types = self.p.parse_types_from_source(source)
		assert types.types['foo'].members[0].type.type_class == TypeClass.EnumerationTypeClass
		assert types.types['foo'].members[1].type.type_class == TypeClass.StructureTypeClass
		assert types.types['foo'].members[1].type.type == StructureVariant.StructStructureType
		assert types.types['foo'].members[2].type.type_class == TypeClass.StructureTypeClass
		assert types.types['foo'].members[2].type.type == StructureVariant.ClassStructureType
		assert types.types['foo'].members[3].type.type_class == TypeClass.StructureTypeClass
		assert types.types['foo'].members[3].type.type == StructureVariant.UnionStructureType
		assert types.types['foo'].members[0].type.members[0].name == 'a'
		assert types.types['foo'].members[0].type.members[1].name == 'b'
		assert types.types['foo'].members[0].type.members[2].name == 'c'
		assert types.types['foo'].members[1].type.members[0].name == 'a'
		assert types.types['foo'].members[2].type.members[0].name == 'a'
		assert types.types['foo'].members[3].type.members[0].name == 'a'
		assert types.types['foo'].members[3].type.members[1].name == 'b'

	def test_forward_declared(self):
		# Via #2431 with a little extra sauce on LIST_ENTRY1
		source = r'''
			struct _LIST_ENTRY;
			typedef struct _LIST_ENTRY LIST_ENTRY;
			typedef LIST_ENTRY LIST_ENTRY1;
			struct _LIST_ENTRY {
				LIST_ENTRY * ForwardLink;
				LIST_ENTRY * BackLink;
			};
			
			struct Test {
				long long Signature;
				LIST_ENTRY1 Link;
				int Action;
				short DefaultId;
			};
		'''
		types = self.p.parse_types_from_source(source)
		assert types.types['_LIST_ENTRY'].width == 0x10
		assert types.types['LIST_ENTRY'].width == 0x10
		assert types.types['LIST_ENTRY1'].width == 0x10
		assert types.types['Test'].width == 0x20
		assert types.types['Test'].members[2].offset == 0x18

	def test_custom_subclass(self):
		class MyTypeParser(TypeParser):
			name = "MyTypeParser"

			def preprocess_source(
					self, source: str, file_name: str, platform: binaryninja.Platform,
					existing_types: Optional[List[QualifiedNameTypeAndId]],
					options: Optional[List[str]], include_dirs: Optional[List[str]]
			) -> Tuple[Optional[str], List[TypeParserError]]:
				return (
					source,
					[
						TypeParserError(TypeParserErrorSeverity.WarningSeverity, "Test Warning", "sources.hpp", 1, 1)
					]
				)

			def parse_types_from_source(
					self,
					source: str,
					file_name: str,
					platform: binaryninja.Platform,
					existing_types: Optional[List[QualifiedNameTypeAndId]],
					options: Optional[List[str]],
					include_dirs: Optional[List[str]],
					auto_type_source: str = ""
			) -> Tuple[Optional[TypeParserResult], List[TypeParserError]]:
				return (
					TypeParserResult(
						[
							ParsedType("my_type", Type.int(4, False), True)
						], [
							ParsedType("my_variable", Type.int(4, False), True)
						], [
							ParsedType("my_function", Type.function(Type.void(), []), True)
						]
					),
					[
						TypeParserError(TypeParserErrorSeverity.WarningSeverity, "Test Warning", "sources.hpp", 1, 1)
					]
				)

			def parse_type_string(
					self, source: str, platform: binaryninja.Platform,
					existing_types: Optional[List[QualifiedNameTypeAndId]]
			) -> Tuple[Optional[Tuple[QualifiedNameType, binaryninja.Type]],
					   List[TypeParserError]]:
				return (
					("my_type", Type.int(4, False)),
					[
						TypeParserError(TypeParserErrorSeverity.WarningSeverity, "Test Warning", "sources.hpp", 1, 1)
					]
				)

		MyTypeParser().register()

		tp = TypeParser['MyTypeParser']
		(result, errors) = tp.preprocess_source('some test source', 'source.h', Platform['windows-x86'])
		assert result is not None
		assert result == 'some test source'

		assert errors is not None
		assert len(errors) == 1

		assert errors[0].severity == TypeParserErrorSeverity.WarningSeverity
		assert errors[0].message == "Test Warning"
		assert errors[0].file_name == "sources.hpp"
		assert errors[0].line == 1
		assert errors[0].column == 1

		(result, errors) = tp.parse_types_from_source('some test source', 'source.h', Platform['windows-x86'])
		assert result is not None
		assert len(result.types) == 1
		assert len(result.variables) == 1
		assert len(result.functions) == 1

		assert result.types[0].name == 'my_type'
		assert result.types[0].type == Type.int(4, False)
		assert result.types[0].is_user

		assert result.variables[0].name == 'my_variable'
		assert result.variables[0].type == Type.int(4, False)
		assert result.variables[0].is_user

		assert result.functions[0].name == 'my_function'
		assert result.functions[0].type == Type.function(Type.void(), [])
		assert result.functions[0].is_user

		assert errors is not None
		assert len(errors) == 1

		assert errors[0].severity == TypeParserErrorSeverity.WarningSeverity
		assert errors[0].message == "Test Warning"
		assert errors[0].file_name == "sources.hpp"
		assert errors[0].line == 1
		assert errors[0].column == 1

		(result, errors) = tp.parse_type_string('some test source', Platform['windows-x86'])
		assert result is not None
		assert result[0] == 'my_type'
		assert result[1] == Type.int(4, False)

		assert errors is not None
		assert len(errors) == 1

		assert errors[0].severity == TypeParserErrorSeverity.WarningSeverity
		assert errors[0].message == "Test Warning"
		assert errors[0].file_name == "sources.hpp"
		assert errors[0].line == 1
		assert errors[0].column == 1


class TestTypePrinter(unittest.TestCase):
	def test_getlines(self):
		arch = 'x86'
		platform = Platform['windows-x86']
		bv = BinaryView.new()
		bv.platform = platform

		types = [
			(Type.int(4), 'basic_int', 'typedef int32_t basic_int;\n'),
			(Type.array(Type.int(4), 4), 'basic_array', 'typedef int32_t basic_array[0x4];\n'),
			(Type.pointer(platform.arch, Type.array(
				Type.int(4), 4
			)), 'pointer_array', 'typedef int32_t (* pointer_array)[0x4];\n'),
			(Type.array(
				Type.pointer(platform.arch, Type.int(4)), 4
			), 'array_pointer', 'typedef int32_t* array_pointer[0x4];\n'),
			(Type.function(
				Type.int(4), []
			), 'basic_func', 'typedef int32_t basic_func();\n'),
			(Type.function(
				Type.int(4), [], platform.fastcall_calling_convention
			), 'convention_func', 'typedef int32_t __fastcall convention_func();\n'),
			(Type.pointer(platform.arch, Type.function(
				Type.int(4), []
			), True), 'const_func_pointer', 'typedef int32_t (* const const_func_pointer)();\n'),
			(Type.pointer(platform.arch, Type.function(
				Type.int(4), []
			)), 'basic_func_pointer', 'typedef int32_t (* basic_func_pointer)();\n'),
			(Type.function(
				Type.pointer(platform.arch, Type.int(4)), []
			), 'func_returning_ptr', 'typedef int32_t* func_returning_ptr();\n'),
			(Type.structure([
				(Type.int(4), 'foo')
			]), 'basic_struct', 'struct basic_struct\n{\n    int32_t foo;\n};\n'),
			(Type.pointer(platform.arch, Type.structure([
				(Type.int(4), 'foo')
			])), 'pointer_struct', 'typedef struct { int32_t foo; }* pointer_struct;\n'),
			(Type.pointer(platform.arch, Type.structure([
				(Type.pointer(platform.arch, Type.int(4)), 'foo')
			])), 'pointer_in_pointer_struct', 'typedef struct { int32_t* foo; }* pointer_in_pointer_struct;\n'),
			(Type.pointer(platform.arch, Type.structure([
				(Type.pointer(platform.arch, Type.structure([
					(Type.pointer(platform.arch, Type.int(4)), 'foo')
				])), 'foo')
			])), 'nested_pointer_struct', 'typedef struct { struct { int32_t* foo; }* foo; }* nested_pointer_struct;\n'),
			(Type.pointer(platform.arch, Type.structure([
				(Type.pointer(platform.arch, Type.function(Type.int(4), [('param', Type.int(4))])), 'foo')
			])), 'pointer_function_struct', 'typedef struct { int32_t (* foo)(int32_t param); }* pointer_function_struct;\n'),
			(Type.pointer(platform.arch, Type.enumeration(platform.arch, [
				('one', 1)
			])), 'pointer_enumeration', 'typedef enum {}* pointer_enumeration;\n'),
		]

		for t in types:
			with self.subTest(t[1]):
				lines = t[0].get_lines(bv, t[1])
				text = ""
				for l in lines:
					for tok in l.tokens:
						text += tok.text
					text += "\n"
				assert text == t[2], f"Invalid printing of type, got {text} expected {t[2]}"


	def test_custom_subclass(self):
		class MyTypePrinter(TypePrinter):
			name = "MyTypePrinter"

			def get_type_tokens(self, type: types.Type, platform: Optional[Platform], name: types.QualifiedName,
								base_confidence: int, escaping: TokenEscapingType) -> List[InstructionTextToken]:
				return [
					InstructionTextToken(InstructionTextTokenType.TextToken, "the type is: ", 0),
					InstructionTextToken(InstructionTextTokenType.TypeNameToken, str(name), 0),
					InstructionTextToken(InstructionTextTokenType.TextToken, " bottom text", 0)
				]

			def get_type_tokens_before_name(self, type: types.Type, platform: Optional[Platform], base_confidence: int,
											parent_type: Optional[types.Type], escaping: TokenEscapingType) -> List[
				InstructionTextToken]:
				return [
					InstructionTextToken(InstructionTextTokenType.TextToken, "the type is: ", 0),
				]

			def get_type_tokens_after_name(self, type: types.Type, platform: Optional[Platform], base_confidence: int,
										   parent_type: Optional[types.Type], escaping: TokenEscapingType) -> List[InstructionTextToken]:
				return [
					InstructionTextToken(InstructionTextTokenType.TextToken, " bottom text", 0),
				]

			def get_type_string(self, type: types.Type, platform: Optional[Platform], name: types.QualifiedName,
								escaping: TokenEscapingType) -> str:
				return f"the type is: {name} bottom text"

			def get_type_string_before_name(self, type: types.Type, platform: Optional[Platform],
											escaping: TokenEscapingType) -> str:
				return f"the type is: "

			def get_type_string_after_name(self, type: types.Type, platform: Optional[Platform],
										   escaping: TokenEscapingType) -> str:
				return f" bottom text"

			def get_type_lines(self, type: types.Type, data: binaryview.BinaryView, name: types.QualifiedName, line_width,
							   collapsed, escaping: TokenEscapingType) -> List[types.TypeDefinitionLine]:
				return [
					TypeDefinitionLine(TypeDefinitionLineType.TypedefLineType, [
						InstructionTextToken(InstructionTextTokenType.TextToken, "the type is: ", 0),
						InstructionTextToken(InstructionTextTokenType.TypeNameToken, str(name), 0),
						InstructionTextToken(InstructionTextTokenType.TextToken, " bottom text", 0)
					], type, type, '', 0, 1)
				]

		MyTypePrinter().register()

		tp = TypePrinter['MyTypePrinter']
		result = tp.get_type_tokens(Type.void(), None, QualifiedName(['test']), 255, TokenEscapingType.NoTokenEscapingType)
		assert result is not None
		assert len(result) == 3
		assert result[0].text == "the type is: "
		assert result[1].text == "test"
		assert result[2].text == " bottom text"
		result = tp.get_type_tokens_before_name(Type.void())
		assert result is not None
		assert len(result) == 1
		assert result[0].text == "the type is: "
		result = tp.get_type_tokens_after_name(Type.void())
		assert result is not None
		assert len(result) == 1
		assert result[0].text == " bottom text"
		result = tp.get_type_string(Type.void(), None, QualifiedName(['test']))
		assert result is not None
		assert result == "the type is: test bottom text"
		result = tp.get_type_string_before_name(Type.void())
		assert result is not None
		assert result == "the type is: "
		result = tp.get_type_string_after_name(Type.void())
		assert result is not None
		assert result == " bottom text"
		result = tp.get_type_lines(Type.void(), BinaryView.new(b''), QualifiedName(['test']))
		assert result is not None
		assert len(result) == 1
		assert len(result[0].tokens) == 3
		assert result[0].tokens[0].text == "the type is: "
		assert result[0].tokens[1].text == "test"
		assert result[0].tokens[2].text == " bottom text"


class TestQualifiedName(unittest.TestCase):
	def test_constructors_and_equality(self):
		assert QualifiedName("name").name == ["name"]
		assert QualifiedName(b"name").name == ["name"]
		assert QualifiedName(QualifiedName("name")).name == ["name"]
		assert QualifiedName(["name1", "name2"]).name == ["name1", "name2"]
		assert QualifiedName([b"name1", b"name2"]).name == ["name1", "name2"]

	def test_comparison(self):
		assert QualifiedName("a") == "a"
		assert QualifiedName(["a", "b"]) == "a::b"
		assert QualifiedName("a") == ["a"]
		assert QualifiedName("a") == QualifiedName("a")
		assert QualifiedName("a").__eq__(None) == NotImplemented
		assert QualifiedName(["a", "b"]) != "a::a"
		assert QualifiedName("a") != ["b"]
		assert QualifiedName("a") != QualifiedName("b")
		assert QualifiedName("a").__ne__(None) == NotImplemented

		assert QualifiedName("a") < QualifiedName("b")
		assert QualifiedName("a").__lt__(None) == NotImplemented
		assert QualifiedName("a") <= QualifiedName("a")
		assert QualifiedName("a").__le__(None) == NotImplemented
		assert QualifiedName("b") > QualifiedName("a")
		assert QualifiedName("a").__gt__(None) == NotImplemented
		assert QualifiedName("a") >= QualifiedName("a")
		assert QualifiedName("a").__ge__(None) == NotImplemented

	def test_accessors(self):
		assert QualifiedName("a")[0] == "a"
		name = ["a", "b", "c"]
		q = QualifiedName(name)
		it = iter(q)
		assert next(it) == "a"
		assert next(it) == "b"
		assert next(it) == "c"
		assert q.name == name
		q.name = list(reversed(name))
		assert q.name == list(reversed(name))

	def test_str(self):
		name = ["a", "b", "c"]
		q = QualifiedName(name)
		assert str(q) == "::".join(name)

	def test_len(self):
		name = ["a", "b", "c"]
		assert len(QualifiedName(name)) == 3


class TypeTest(unittest.TestCase):
	def setUp(self) -> None:
		self.arch = Architecture['x86_64']
		self.plat = Platform['x86_64']
		self.cc = self.plat.calling_conventions[0]

	def test_IntegerBuilder(self):
		ib = TypeBuilder.int(4)
		ib.const = True
		ib.volatile = False
		ib.alternate_name = "billy bob"
		ib.signed = True
		assert ib.const
		assert not ib.volatile
		assert ib.alternate_name == "billy bob"
		assert ib.signed
		assert len(ib) == 4
		assert ib == ib.immutable_copy().mutable_copy(), "IntegerBuilder failed to round trip mutability"
		assert repr(ib).startswith("<type:")

	def test_CharBuilder(self):
		b = TypeBuilder.char("my_char")
		b.const = True
		b.volatile = False
		assert b.alternate_name == "my_char"
		b.alternate_name = "my_char2"
		assert b.const
		assert not b.volatile
		assert b.alternate_name == "my_char2"
		assert b == b.immutable_copy().mutable_copy(), "CharBuilder failed to round trip mutability"

	def test_FloatBuilder(self):
		b = TypeBuilder.float(4, "half")
		b.const = True
		b.volatile = False
		assert b.const
		assert not b.volatile
		assert b.alternate_name == "half"
		assert b == b.immutable_copy().mutable_copy(), "FloatBuilder failed to round trip mutability"

	def test_WideCharBuilder(self):
		b = TypeBuilder.wide_char(4, "wchar32_t")
		b.const = True
		b.volatile = False
		assert b.const
		assert not b.volatile
		assert b.alternate_name == "wchar32_t"
		assert b == b.immutable_copy().mutable_copy(), "WideCharBuilder failed to round trip mutability"

	def test_PointerBuilder(self):
		ib = TypeBuilder.int(4)
		b = TypeBuilder.pointer(self.arch, ib, 4)
		b.const = True
		b.volatile = False
		assert ib.immutable_copy() == b.immutable_target
		assert ib == b.target
		assert ib.immutable_copy() == b.child.immutable_copy()
		assert b == b.immutable_copy().mutable_copy(), "PointerBuilder failed to round trip mutability"

		b = TypeBuilder.pointer_of_width(4, ib)
		b.const = True
		b.volatile = False
		assert len(b) == 4
		assert ib.immutable_copy() == b.immutable_target
		assert ib == b.target
		assert ib.immutable_copy() == b.child.immutable_copy()
		assert b == b.immutable_copy().mutable_copy(), "PointerBuilder failed to round trip mutability"
		assert b.mutable_copy() == b
		assert TypeBuilder.create() == NotImplemented

	def test_VoidBuilder(self):
		b = TypeBuilder.void()
		assert b == b.immutable_copy().mutable_copy(), "VoidBuilder failed to round trip mutability"

	def test_BoolBuilder(self):
		b = TypeBuilder.bool()
		assert b == b.immutable_copy().mutable_copy(), "VoidBuilder failed to round trip mutability"

	def test_FunctionBuilder(self):
		bb = TypeBuilder.bool()
		ib = TypeBuilder.int(4)
		pb = TypeBuilder.pointer(self.arch, ib, 4)
		vb = TypeBuilder.void()
		b = TypeBuilder.function(vb, [FunctionParameter(pb, "arg1"), ("arg2", pb)], self.cc)
		assert b.system_call_number is None
		b.system_call_number = 1
		assert b.system_call_number == 1
		b.clear_system_call()
		assert b.system_call_number is None
		b.system_call_number = 1

		assert b == b.immutable_copy().mutable_copy(), "FunctionBuilder failed to round trip mutability"
		assert b.immutable_return_value == vb.immutable_copy()
		assert b.return_value == vb
		b.return_value = b
		b.append(bb)
		b.append(FunctionParameter(pb, "arg3"))
		assert b.calling_convention == self.cc
		assert b.can_return
		b.can_return = False
		assert not b.can_return
		assert b.stack_adjust == 0
		assert len(b.parameters) == 4
		assert b.parameters[0].type == pb.immutable_copy()
		assert b.parameters[0].name == "arg1"
		assert b.parameters[2].type == bb.immutable_copy()
		assert b.parameters[2].name == ""
		assert b.parameters[3].type == pb.immutable_copy()
		assert b.parameters[3].name == "arg3"
		assert b.stack_adjust.value == 0
		assert not b.variable_arguments
		b.parameters = [FunctionParameter(pb, "arg1")]
		assert b.parameters[0].type == pb.immutable_copy()
		assert b.parameters[0].name == "arg1"
		assert len(b.parameters) == 1

		b = TypeBuilder.function()
		assert len(b.parameters) == 0
		assert b.return_value == TypeBuilder.void()
		assert b == b.immutable_copy().mutable_copy(), "FunctionBuilder failed to round trip mutability"

	def test_ArrayBuilder(self):
		ib = TypeBuilder.int(4)
		b = TypeBuilder.array(ib, 4)
		assert len(b) == len(ib) * 4
		assert b.count == 4
		assert b.element_type == ib
		assert b == b.immutable_copy().mutable_copy(), "ArrayBuilder failed to round trip mutability"

	def test_StructureBuilder(self):
		ib = TypeBuilder.int(4)
		b = TypeBuilder.structure([StructureMember(ib, "name", 0), Type.bool()])
		b.members = [*b.members, StructureMember(ib, "name2", 8)]
		assert not b.union
		b.type = StructureVariant.UnionStructureType
		assert b.union
		b.type = StructureVariant.StructStructureType
		assert b['name'].name == "name"
		assert b['name'].type == ib.immutable_copy()

		assert b["doesnt exist"] is None

		it = iter(b)
		mem = next(it)
		assert mem.name == "name"
		assert mem.type == ib.immutable_copy()
		mem = next(it)
		assert mem.name == "field_4"
		assert mem.type == Type.bool()
		mem = next(it)
		assert mem.name == "name2"
		assert mem.type == ib.immutable_copy()

		assert len(b) == 12
		assert b.member_at_offset(0x1000) == None
		assert b.member_at_offset(0).name == "name"
		assert b.member_at_offset(0).type == ib.immutable_copy()
		assert b.member_at_offset(4).name == "field_4"
		assert b.member_at_offset(4).type == Type.bool()
		assert b.member_at_offset(8).name == "name2"
		assert b.member_at_offset(8).type == ib.immutable_copy()
		assert b.index_by_name("name") == 0
		assert b.index_by_name("name2") == 2
		assert b.index_by_name("doesn't exist") is None
		assert b.index_by_offset(0) == 0
		assert b.index_by_offset(4) == 1
		assert b.index_by_offset(8) == 2
		assert b.index_by_offset(0x10000) is None
		b.add_member_at_offset("foo", Type.int(4), 0x20)
		mem = b.member_at_offset(0x20)
		assert mem.name == "foo"
		assert mem.type == Type.int(4)
		assert b == b.immutable_copy().mutable_copy(), "StructureBuilder failed to round trip mutability"

		assert len(StructureMember(Type.int(4), "foo", 0)) == len(Type.int(4))

		b = TypeBuilder.union([StructureMember(ib, "name", 0), StructureMember(ib, "name2", 0)])
		assert b.type == StructureVariant.UnionStructureType

		b = TypeBuilder.class_type([StructureMember(ib, "name", 0), StructureMember(ib, "name2", 4)])
		assert b.type == StructureVariant.ClassStructureType

	def test_EnumerationBuilder(self):
		b = EnumerationBuilder.create([("Member1", 1)], 4, None, False)
		assert not b.signed
		b.signed = True
		assert b.signed
		assert len(b.members) == 1
		assert b.members[0].name == "Member1"
		assert b.members[0].value == 1
		b.members = [("Member0", 0), ("Member1")]
		assert b.members[0].name == "Member0"
		assert b.members[0].value == 0
		assert b.members[1].name == "Member1"
		assert b.members[1].value == None

		b.append("NewMember")
		assert b.members[2].name == "NewMember"
		assert b.members[2].value == None
		it = iter(b)
		mem = next(it)
		assert mem.name == "Member0"
		assert mem.value == 0
		mem = next(it)
		assert mem.name == "Member1"
		assert mem.value == None
		mem = next(it)
		assert mem.name == "NewMember"
		assert mem.value == None

		assert b["Member0"].name == "Member0"
		assert b["Member0"].value == 0
		assert b["Member1"].name == "Member1"
		assert b["Member1"].value == None
		assert b["NewMember"].name == "NewMember"
		assert b["NewMember"].value == None
		assert b[0].name == "Member0"
		assert b[0].value == 0
		assert b[1].name == "Member1"
		assert b[1].value == None

		mem0, mem1 = b[0:2]
		assert mem0.name == "Member0"
		assert mem0.value == 0
		assert mem1.name == "Member1"
		assert mem1.value == None
		self.assertRaises(ValueError, lambda: b[None])

		b["Member0"] = 4
		assert b["Member0"].value == 4
		b[1] = EnumerationMember("Member10", 10)
		assert b[1].name == "Member10"
		assert b[1].value == 10
		assert b["Member_doesn't exist"] == None
		self.assertRaises(ValueError, lambda: b.__setitem__(None, None))

		e1 = EnumerationMember("Member10", 10)
		assert e1.value == 10
		assert e1.name == "Member10"
		assert int(e1) == 10
		assert repr(e1).endswith("<Member10 = 0xa>")

	def test_NamedTypeReferenceBuilder(self):
		b = TypeBuilder.named_type_reference(NamedTypeReferenceClass.UnknownNamedTypeClass, "foo")
		assert b.name == "foo"
		assert b.named_type_class == NamedTypeReferenceClass.UnknownNamedTypeClass

		b = TypeBuilder.named_type_from_type("foobar", NamedTypeReferenceClass.UnknownNamedTypeClass)
		assert b.name == "foobar"
		assert b.id == b.type_id
		assert b.named_type_class == NamedTypeReferenceClass.UnknownNamedTypeClass
		assert b == b.immutable_copy().mutable_copy(), "NamedTypeReferenceBuilder failed to round trip mutability"

		b = TypeBuilder.named_type_from_type_and_id("type_id", QualifiedName(b"name"), Type.int(4))
		assert b.name == "name"
		assert b.id == "type_id"
		assert b.named_type_class == NamedTypeReferenceClass.TypedefNamedTypeClass
		assert repr(b).startswith("<type: mutable:NamedTypeReferenceClass 'typedef")

		b = TypeBuilder.named_type_from_type_and_id("type_id", QualifiedName(b"name"))
		assert b.name == "name"
		assert b.id == "type_id"
		assert b.named_type_class == NamedTypeReferenceClass.UnknownNamedTypeClass
		assert repr(b).startswith("<type: mutable:NamedTypeReferenceClass 'unknown")

		enm = TypeBuilder.enumeration(self.arch, [("Member1", 0)], 4, False)
		b = TypeBuilder.named_type_from_type_and_id("type_id", QualifiedName(b"name"), enm)
		assert b.name == "name"
		assert b.id == "type_id"
		assert b.named_type_class == NamedTypeReferenceClass.EnumNamedTypeClass
		assert repr(b).startswith("<type: mutable:NamedTypeReferenceClass 'enum")

		str = TypeBuilder.structure([], True, StructureVariant.StructStructureType)
		b = TypeBuilder.named_type_from_type_and_id("type_id", QualifiedName(b"name"), str)
		assert b.name == "name"
		assert b.id == "type_id"
		assert b.named_type_class == NamedTypeReferenceClass.StructNamedTypeClass
		assert repr(b).startswith("<type: mutable:NamedTypeReferenceClass 'struct")

		str = TypeBuilder.structure([], True, StructureVariant.ClassStructureType)
		b = TypeBuilder.named_type_from_type_and_id("type_id", QualifiedName(b"name"), str)
		assert b.name == "name"
		assert b.id == "type_id"
		assert b.named_type_class == NamedTypeReferenceClass.ClassNamedTypeClass
		assert repr(b).startswith("<type: mutable:NamedTypeReferenceClass 'class")

		str = TypeBuilder.structure([], True, StructureVariant.UnionStructureType)
		b = TypeBuilder.named_type_from_type_and_id("type_id", QualifiedName([b"name", b"name"]), str)
		assert b.name == QualifiedName(["name", "name"])
		assert b.id == "type_id"
		assert b.named_type_class == NamedTypeReferenceClass.UnionNamedTypeClass
		assert repr(b).startswith("<type: mutable:NamedTypeReferenceClass 'union")

		b = NamedTypeReferenceBuilder.named_type(b, 4, 4)
		assert b.width == 4
		assert b.alignment == 4

		b = NamedTypeReferenceBuilder.named_type_from_type("name")
		b.named_type_class == NamedTypeReferenceClass.UnknownNamedTypeClass

		# need binary view for this one
		#b = NamedTypeReferenceBuilder.named_type_from_registered_type(bv, )

	def test_IntegerType(self):
		t = IntegerType.create(2, False, "", self.plat, 0)
		assert t.width == 2
		assert len(t) == 2
		assert t.alignment == 2
		assert t.__ne__(None) == NotImplemented
		assert t.offset == 0
		assert t.confidence == 0
		assert [str(i) for i in t.get_tokens()] == ["uint16_t"]
		assert [str(i) for i in t.get_tokens_before_name()] == ["uint16_t"]
		assert [str(i) for i in t.get_tokens_after_name()] == []
		assert t.platform == self.plat
		tc = t.with_confidence(255)
		assert tc.confidence == 255

		t = Type.int(4)
		assert t.width == 4
		assert len(t) == 4
		assert t.alignment == 4
		assert t.altname == ""
		assert t.mutable_copy().immutable_copy() == t

	def test_VoidType(self):
		t = Type.void()
		assert t.width == 0
		assert t.altname == ""
		assert t.mutable_copy().immutable_copy() == t

	def test_BoolType(self):
		t = Type.bool()
		assert t.width == 1
		assert t.altname == ""
		assert t.mutable_copy().immutable_copy() == t

	def test_CharType(self):
		t = Type.char()
		assert t.width == 1
		assert t.altname == ""
		assert t.mutable_copy().immutable_copy() == t

		t = Type.char("char_alt_name")
		assert t.width == 1
		assert t.altname == "char_alt_name"
		assert t.mutable_copy().immutable_copy() == t

	def test_FloatType(self):
		t = Type.float(2)
		assert str(t.tokens[0]) == "float16"
		assert len(t) == 2
		t = Type.float(4)
		assert str(t.tokens[0]) == "float"
		assert len(t) == 4
		t = Type.float(8)
		assert str(t.tokens[0]) == "double"
		assert len(t) == 8
		t = Type.float(10)
		assert str(t.tokens[0]) == "long double"
		assert len(t) == 10
		t = Type.float(16)
		assert str(t.tokens[0]) == "float128"
		assert len(t) == 16
		assert t.mutable_copy().immutable_copy() == t

	def test_WideCharType(self):
		t = Type.wide_char(4)
		assert len(t) == 4
		assert str(t.tokens[0]) == "wchar32"
		assert t.mutable_copy().immutable_copy() == t

	def test_PointerType(self):
		t = Type.pointer(self.arch, Type.int(4), True, True)
		assert t.const
		assert t.volatile
		assert t.target == Type.int(4)
		assert t.mutable_copy().immutable_copy() == t
		assert t.ref_type == ReferenceType.PointerReferenceType
		t = Type.pointer_of_width(4, Type.int(4))
		assert len(t) == 4

	def test_ArrayType(self):
		element_type = Type.int(4)
		t = Type.array(element_type, 4)
		assert t.count == 4
		assert len(t) == 16
		assert t.element_type == element_type
		assert t.mutable_copy().immutable_copy() == t

	def test_StructureType(self):
		t = Type.structure_type(StructureBuilder.create([Type.int(1)]))
		assert t.mutable_copy().immutable_copy() == t
		t = Type.structure()
		assert t.mutable_copy().immutable_copy() == t
		assert t.mutable_copy().immutable_copy() == t
		t = Type.structure([Type.int(4)])
		assert t.mutable_copy().immutable_copy() == t
		t1 = t
		t = Type.structure([
		    StructureMember(Type.int(4), "first", 0, MemberAccess.PublicAccess, MemberScope.StaticScope),
		    StructureMember(Type.int(4), "second", 4, MemberAccess.PublicAccess, MemberScope.StaticScope)
		])
		t2 = t
		self.assertRaises(ValueError, lambda: Type.structure([None]))
		assert hash(t1) != hash(t2)
		assert t["first"].name == "first"
		assert t["second"].name == "second"
		self.assertRaises(ValueError, lambda: t["not there"])
		mem = t.member_at_offset(0)
		assert mem.name == "first"
		assert mem.type == Type.int(4)
		assert mem.access == MemberAccess.PublicAccess
		assert mem.scope == MemberScope.StaticScope
		self.assertRaises(ValueError, lambda: t.member_at_offset(-1))
		assert not t.packed

		t = Type.union([
		    StructureMember(Type.int(4), "first", 0, MemberAccess.PublicAccess, MemberScope.StaticScope),
		    StructureMember(Type.int(4), "second", 4, MemberAccess.PublicAccess, MemberScope.StaticScope)
		])
		ntr = t.generate_named_type_reference("guid", "name")
		assert ntr.name == "name"

		t = Type.class_type([
		    StructureMember(Type.int(4), "first", 0, MemberAccess.PublicAccess, MemberScope.StaticScope),
		    StructureMember(Type.int(4), "second", 4, MemberAccess.PublicAccess, MemberScope.StaticScope)
		])
		ntr = t.generate_named_type_reference("guid", "name")
		assert ntr.name == "name"

	def test_NamedTypeReferenceType(self):
		t = Type.named_type(
		    NamedTypeReferenceBuilder.create(NamedTypeReferenceClass.UnknownNamedTypeClass, "id", "name")
		)
		assert t.mutable_copy().immutable_copy() == t
		t = Type.named_type_from_type_and_id("id2", ["qualified", "name"])
		assert t.mutable_copy().immutable_copy() == t
		t = Type.generate_named_type_reference("guid", [b"byte", b"name"])
		assert t.mutable_copy().immutable_copy() == t

		b = Type.named_type_reference(NamedTypeReferenceClass.UnknownNamedTypeClass, "name")
		assert b.name == "name"
		assert b.named_type_class == NamedTypeReferenceClass.UnknownNamedTypeClass
		assert repr(b).startswith("<type: immutable:NamedTypeReferenceClass 'unknown")

		b = Type.named_type_reference(NamedTypeReferenceClass.EnumNamedTypeClass, "name")
		assert b.name == "name"
		assert b.named_type_class == NamedTypeReferenceClass.EnumNamedTypeClass
		assert repr(b).startswith("<type: immutable:NamedTypeReferenceClass 'enum")

		b = Type.named_type_reference(NamedTypeReferenceClass.StructNamedTypeClass, "name")
		assert b.name == "name"
		assert b.named_type_class == NamedTypeReferenceClass.StructNamedTypeClass
		assert repr(b).startswith("<type: immutable:NamedTypeReferenceClass 'struct")

		b = Type.named_type_reference(NamedTypeReferenceClass.ClassNamedTypeClass, "name")
		assert b.name == "name"
		assert b.named_type_class == NamedTypeReferenceClass.ClassNamedTypeClass
		assert repr(b).startswith("<type: immutable:NamedTypeReferenceClass 'class")

		b = Type.named_type_reference(NamedTypeReferenceClass.UnionNamedTypeClass, "name")
		assert b.name == "name"
		assert b.named_type_class == NamedTypeReferenceClass.UnionNamedTypeClass
		assert repr(b).startswith("<type: immutable:NamedTypeReferenceClass 'union")

		b = NamedTypeReferenceType.generate_auto_type_ref(NamedTypeReferenceClass.UnionNamedTypeClass, "foo", "bar")
		assert b.type_id.startswith("foo")
		assert b.name == "bar"
		assert b.named_type_class == NamedTypeReferenceClass.UnionNamedTypeClass
		b = NamedTypeReferenceType.generate_auto_demangled_type_ref(NamedTypeReferenceClass.UnionNamedTypeClass, "bar")
		assert b.type_id.startswith("demange")

	def test_EnumerationType(self):
		t = Type.enumeration_type(self.arch, EnumerationBuilder.create([("Member1", 1)]))
		t2 = Type.enumeration_type(self.arch, EnumerationBuilder.create([("Member2", 2)]))
		assert t.mutable_copy().immutable_copy() == t
		assert t.members[0].name == "Member1"
		assert t.members[0].value == 1
		self.assertRaises(ValueError, lambda: Type.enumeration())
		self.assertRaises(ValueError, lambda: Type.enumeration(width=0))
		t = t.generate_named_type_reference("guid", "name")
		assert t.type_id == "guid"
		assert t.name == "name"
		assert hash(t2) != hash(t)
		assert Type.enumeration(members=[EnumerationMember("asdf")], width=4).members[0].value is None

	def test_FunctionType(self):
		t = Type.function()
		assert t.mutable_copy().immutable_copy() == t
		self.assertRaises(ValueError, lambda: t.mutable_copy() == t)

		vnt = VariableNameAndType(VariableSourceType.StackVariableSourceType, 0, 0, "arg1", Type.int(4))
		param1 = FunctionParameter(Type.int(4), "arg1", vnt)
		vnt = VariableNameAndType(VariableSourceType.RegisterVariableSourceType, 0, 0, "arg2", Type.int(4))
		param2 = FunctionParameter(Type.int(4), "arg2", vnt)
		vnt = VariableNameAndType(VariableSourceType.FlagVariableSourceType, 0, 0, "arg3", Type.int(4))
		param3 = FunctionParameter(Type.int(4), "arg3", vnt)
		t = Type.function(Type.void(), [param1, param2, param3], self.cc)
		assert param3 == param3.mutable_copy().immutable_copy()
		assert repr(param3).endswith(param3.name)
		assert t.mutable_copy().immutable_copy() == t
		assert t.stack_adjustment == 0
		assert t.return_value == Type.void()
		assert t.calling_convention == self.cc
		assert not t.has_variable_arguments
		assert t.can_return


class TestOffsetWithConfidence(unittest.TestCase):
	def test_constructor(self):
		o = OffsetWithConfidence(0)
		assert o.value == 0
		assert o.confidence == 255
		assert int(o) == 0
		assert o == 0
		assert o == OffsetWithConfidence(0)
		assert o != OffsetWithConfidence(0, 0)
		assert o < 1
		assert o <= 0
		assert o > -1
		assert o >= 0


class TestBoolWithConfidence(unittest.TestCase):
	def test_constructor(self):
		o = BoolWithConfidence(True)
		assert o.value == True
		assert o.confidence == 255
		assert bool(o) == True
		assert o == True
		assert o == BoolWithConfidence(True)
		assert o != BoolWithConfidence(True, 0)


class TestSymbols(unittest.TestCase):
	def test_CoreSymbol(self):
		with Apparatus("helloworld") as bv:
			assert len(bv.symbols) == 56
			sym = bv.symbols["_Jv_RegisterClasses"][0]
			sym2 = bv.symbols['__elf_header'][0]
			assert repr(sym).startswith('<ExternalSymbol: "_Jv_RegisterClasses" @ 0x11038>')
			assert sym == sym
			assert sym != sym2
			assert sym.__eq__(None) == NotImplemented
			assert sym.__ne__(None) == NotImplemented
			assert hash(sym) != hash(sym2)
			assert sym.binding == SymbolBinding.WeakBinding
			assert sym.short_name == "_Jv_RegisterClasses"
			assert sym.full_name == "_Jv_RegisterClasses"
			assert sym.raw_name == "_Jv_RegisterClasses"
			assert sym.raw_bytes == b"_Jv_RegisterClasses"
			assert sym.ordinal == 0
			assert sym.auto
			sym = Symbol(
			    "DataSymbol", 0, "short_name", "full_name", "raw_name", SymbolBinding.GlobalBinding,
			    NameSpace("BN_INTERNAL_NAMESPACE"), 2
			)
			assert sym.binding == SymbolBinding.GlobalBinding
			assert sym.short_name == "short_name"
			assert sym.full_name == "full_name"
			assert sym.raw_name == "raw_name"
			assert sym.raw_bytes == b"raw_name"
			assert sym.ordinal == 2
			assert not sym.auto

	def test_NameSpace(self):
		ns = NameSpace("BN_INTERNAL_NAMESPACE")
		assert str(ns) == str(NameSpace._from_core_struct(ns._to_core_struct()))


class TestTypes(TestWithBinaryView):
	def test_named_type_from_registered_type(self):
		n = Type.named_type_from_registered_type(self.bv, "Elf32_Dyn")
		assert n.name == "Elf32_Dyn"

	def test_attributes(self):
		t = self.bv.types["Elf32_Dyn"]
		assert t.confidence == 255
		assert t.platform == self.bv.platform
		t.confidence = 0
		assert t.confidence == 0
		p = Platform["windows-x86"]
		t.platform = p
		assert t.platform == p
		with t.get_builder(self.bv) as s:
			assert isinstance(s, StructureBuilder)

		s = self.bv.types["Elf32_Dyn"]
		n = s.registered_name
		assert s == n.target(self.bv)
		unregistered_ntr = NamedTypeReferenceType.generate_auto_demangled_type_ref(
		    NamedTypeReferenceClass.EnumNamedTypeClass, "foobar"
		)
		assert unregistered_ntr.target(self.bv) == None


class TestMutableTypeBuilder(TestWithBinaryView):
	def test_MutableTypeBuilder(self):
		with Type.builder(self.bv, "Elf32_Dyn") as b:
			assert isinstance(b, StructureBuilder)
			b.append(Type.int(4), "test_field")

		b = self.bv.types["Elf32_Dyn"]
		assert isinstance(b, StructureType)
		assert b.member_at_offset(8).name == "test_field"

		self.assertRaises(ValueError, lambda: Type.builder(self.bv, None))

		with Type.builder(self.bv, None, 'elf:["Elf32_Dyn"]') as b:
			assert isinstance(b, StructureBuilder)
			b.append(Type.int(4), "test_field2")

		b = self.bv.types["Elf32_Dyn"]
		assert isinstance(b, StructureType)
		assert b.member_at_offset(12).name == "test_field2"

		self.assertRaises(ValueError, lambda: Type.builder(self.bv, None, 'not - elf:["Elf32_Dyn"]'))
		self.assertRaises(ValueError, lambda: Type.builder(self.bv, 'not - elf:["Elf32_Dyn"]'))

		with MutableTypeBuilder(self.bv.types["Elf32_Dyn"].mutable_copy(), self.bv, "Elf32_Dyn", None, 255, False) as b:
			b.append(Type.int(4), "test_field2")


class TestWithFunction(TestWithBinaryView):
	def setUp(self):
		super().setUp()
		self.func = self.bv.get_functions_by_name("main")[0]

	def test_equality(self):
		func1 = self.func
		func2 = self.bv.get_function_at(0x0000848c)
		assert func1 == func1
		assert func1 != func2
		assert func1.start < 0x0000848c
		assert func1 < func2
		assert func1 <= func2
		assert func2 > func1
		assert func2 >= func1

	def test_getters(self):
		assert isinstance(self.func[0], BasicBlock)
		it = iter(self.func)
		assert isinstance(next(it), BasicBlock)
		assert next(it) in self.func
		assert self.func.start in self.func

	def test_str(self):
		assert str(self.func) == "int32_t main(int32_t argc, char** argv, char** envp)"

	def test_indexing(self):
		first_block = self.func[0]
		assert first_block.start == self.func.start
		assert first_block.start == 0x8440

		second_third = self.func[1:3]
		assert second_third[0].start == 0x846c
		assert second_third[1].start == 0x8460

		self.assertRaises(IndexError, lambda: self.func[5])
		self.assertRaises(IndexError, lambda: self.func[3:6])
		self.assertRaises(ValueError, lambda: self.func['beans'])

	def test_name_symbol(self):
		assert self.func.name == "main"
		my_name = "my_name"
		my_name2 = "my_name"
		self.func.name = my_name
		assert self.func.name == my_name
		self.func.name = Symbol(SymbolType.FunctionSymbol, self.func.start, my_name2)
		assert self.func.name == my_name2
		self.func.name = None
		assert self.func.name == "main"

		sym = self.func.symbol
		assert sym.type == SymbolType.FunctionSymbol
		assert sym.address == self.func.start
		assert sym.name == self.func.name

	def test_view_arch_platform(self):
		assert isinstance(self.bv, BinaryView)
		assert isinstance(self.arch, Architecture)
		assert isinstance(self.plat, Platform)

	def test_size_and_addresses(self):
		assert self.func.total_bytes == 68
		assert self.func.lowest_address == 0x8440
		assert self.func.highest_address == 0x8483
		assert len(self.func.address_ranges) == 1
		assert self.func.address_ranges[0].start == 0x8440
		assert self.func.address_ranges[0].end == 0x8484

	def test_auto(self):
		assert not self.func.auto
		assert not self.func.has_user_annotations
		# cause a user annotation
		self.func.parameter_vars[0].name = "arg_count"
		assert self.func.has_user_annotations

	def test_no_return(self):
		assert self.func.can_return
		self.func.can_return = False
		self.bv.update_analysis_and_wait()
		assert not self.func.can_return
		self.func.can_return = True
		self.bv.update_analysis_and_wait()
		assert self.func.can_return

	def test_explicitly_defined_types(self):
		assert self.func.explicitly_defined_type
		func2 = self.bv.get_function_at(0x0000840c)
		assert not func2.explicitly_defined_type

	def test_needs_update(self):
		assert not self.func.needs_update

	def test_comments(self):
		assert self.func.comments == {}
		self.func.set_comment(0x00008470, "my_comment")
		assert self.func.comments == {0x00008470: 'my_comment'}
		self.func.comment = "Function Level Comment"
		assert self.func.comment == "Function Level Comment"

		msg = "A Comment"
		addr = 0x0000845c
		self.func.set_comment_at(addr, msg)
		assert self.func.get_comment_at(addr) == msg

	def test_create_tag(self):
		msg1 = "Bugs here"
		msg2 = "Crashes here"
		msg3 = "Library here"
		msg4 = "Important here"
		name1 = "Bugs"
		name2 = "Crashes"
		name3 = "Library"
		name4 = "Important"
		tt1 = self.bv.tag_types[name1]
		tt2 = self.bv.tag_types[name2]
		tt3 = self.bv.tag_types[name3]
		tt4 = self.bv.tag_types[name4]
		tag1 = self.func.create_tag(tt1, msg1, True)
		tag2 = self.func.create_user_tag(tt2, msg2)
		tag3 = self.func.create_auto_tag(tt3, msg3)
		tag4 = self.func.create_auto_tag(tt4, msg4)

		assert len(self.func.function_tags) == 0
		self.func.add_user_function_tag(tag1)
		self.func.add_user_function_tag(tag2)
		self.func.add_user_function_tag(tag3)
		t = self.func.create_user_function_tag(tt4, msg4, True)
		t = self.func.create_user_function_tag(tt4, msg4, True)
		tags = self.func.function_tags
		assert len(tags) == 4 == len(self.func.user_function_tags)
		assert tags[0].data == msg1
		assert tags[0].type == tt1
		assert tags[1].data == msg2
		assert tags[1].type == tt2
		assert tags[2].data == msg3
		assert tags[2].type == tt3
		assert tags[3].data == msg4
		assert tags[3].type == tt4
		assert tags[3] == t

		assert 1 == len(self.func.get_function_tags_of_type(tt3))
		assert 1 == len(self.func.get_user_function_tags_of_type(tt4))
		assert 0 == len(self.func.get_auto_function_tags_of_type(tt4))

		self.func.remove_user_function_tag(tags[0])
		self.func.remove_user_function_tag(tags[1])
		self.func.remove_user_function_tag(tags[2])
		self.func.remove_user_function_tag(tags[3])
		assert len(self.func.function_tags) == 0

		addr = self.func.start + 4

		assert len(self.func.address_tags) == 0
		self.func.add_user_address_tag(addr, tag1)
		tags = self.func.address_tags
		assert len(tags) == 1
		_, addr, tag = tags[0]
		assert addr == addr
		assert tag.data == msg1
		assert tag.type == tt1
		self.func.remove_user_address_tag(addr, tag)
		assert len(self.func.address_tags) == 0

		self.assertRaises(TypeError, lambda: self.func.create_user_address_tag(0, None, None))

		t = self.func.create_user_address_tag(addr, tt1, msg1, True)
		t = self.func.create_user_address_tag(addr, tt1, msg1, True)
		tags = self.func.address_tags
		assert len(tags) == 1
		_, addr, tag = tags[0]
		assert t == tag
		assert tag.data == msg1
		assert tag.type == tt1
		self.func.remove_user_address_tag(addr, tag)
		assert len(self.func.address_tags) == 0

		assert len(self.func.function_tags) == 0
		self.func.add_auto_function_tag(tag1)
		t = self.func.create_auto_function_tag(tt2, msg2, True)
		t = self.func.create_auto_function_tag(tt2, msg2, True)
		tags = self.func.function_tags
		assert len(tags) == 2 == len(self.func.auto_function_tags)
		assert tags[0].data == msg1
		assert tags[0].type == tt1
		assert tags[1].data == msg2
		assert tags[1].type == tt2
		assert tags[1] == t
		self.func.remove_auto_function_tag(tags[0])
		self.func.remove_auto_function_tag(tags[1])
		assert len(self.func.function_tags) == 0

		assert len(self.func.address_tags) == 0
		self.func.add_auto_address_tag(addr, tag1)
		t = self.func.create_auto_address_tag(addr, tt2, msg2, True)
		t = self.func.create_auto_address_tag(addr, tt2, msg2, True)
		tags = self.func.address_tags
		assert len(tags) == 2
		assert t == tags[1][2]
		assert tags[0][2].data == msg1
		assert tags[0][2].type == tt1
		assert tags[1][2].data == msg2
		assert tags[1][2].type == tt2

		self.func.get_address_tags_at(addr, self.func.arch)
		assert len(tags) == 2
		assert t == tags[1][2]
		assert tags[0][2].data == msg1
		assert tags[0][2].type == tt1
		assert tags[1][2].data == msg2
		assert tags[1][2].type == tt2

		self.func.remove_auto_address_tag(addr, tags[0][2])
		self.func.remove_auto_address_tag(addr, tags[1][2])
		assert len(self.func.address_tags) == 0

		t = self.func.create_auto_address_tag(addr, tt2, msg2, True)
		t = self.func.create_auto_address_tag(addr + 4, tt2, msg2, True)
		t = self.func.create_user_address_tag(addr, tt1, msg1, True)

		assert 2 == len(self.func.auto_address_tags)
		assert 1 == len(self.func.user_address_tags)

		range = variable.AddressRange(addr, 0x8480)
		all_at = self.func.get_address_tags_in_range(range)
		auto_at = self.func.get_auto_address_tags_in_range(range)
		user_at = self.func.get_user_address_tags_in_range(range)

		assert len(all_at) == 3
		assert len(auto_at) == 2
		assert len(user_at) == 1

		assert 1 == len(self.func.get_auto_address_tags_at(addr))
		assert 1 == len(self.func.get_user_address_tags_at(addr))

		assert 1 == len(self.func.get_address_tags_of_type(addr, tt2))
		assert 0 == len(self.func.get_user_address_tags_of_type(addr, tt2))
		assert 1 == len(self.func.get_address_tags_of_type(addr, tt1))
		assert 0 == len(self.func.get_auto_address_tags_of_type(addr, tt1))

		t = self.func.create_user_address_tag(addr, tt2, msg1, True)
		self.func.remove_user_address_tags_of_type(addr, tt2)
		assert 0 == len(self.func.get_user_address_tags_of_type(addr, tt2))
		assert 1 == len(self.func.get_user_address_tags_of_type(addr, tt1))

		self.func.remove_auto_address_tags_of_type(addr, tt2)
		assert 0 == len(self.func.get_auto_address_tags_of_type(addr, tt2))


	def test_il_properties(self):
		lifted_il = self.func.lifted_il
		assert isinstance(lifted_il, LowLevelILFunction)
		assert lifted_il == self.func.lifted_il_if_available

		llil = self.func.low_level_il
		assert isinstance(llil, LowLevelILFunction)
		assert llil == self.func.llil
		assert llil == self.func.llil_if_available

		mlil = self.func.medium_level_il
		assert isinstance(mlil, MediumLevelILFunction)
		assert mlil == self.func.mlil
		assert mlil == self.func.mlil_if_available

		mmlil = self.func.llil.mapped_medium_level_il
		assert isinstance(mmlil, MediumLevelILFunction)
		assert mmlil == self.func.mmlil
		assert mmlil == self.func.mmlil_if_available

		hlil = self.func.high_level_il
		assert isinstance(hlil, HighLevelILFunction)
		assert hlil == self.func.hlil
		assert hlil == self.func.hlil_if_available

	def test_misc_properties(self):
		callees = self.func.callees
		assert len(callees) == 2

		callers = self.func.callers
		assert len(callers) == 2
		assert callees[0].start == 0x82dc
		assert callees[1].start == 0x82dc

	def test_function_type(self):
		ft = self.func.function_type
		assert ft.return_value == Type.int(4)
		ftm = ft.mutable_copy()
		ftm.return_value = Type.int(4, False)
		self.func.function_type = ftm
		self.func.view.update_analysis_and_wait()
		assert self.func.function_type.return_value == Type.int(4, False), f"{self.func.function_type.return_value} != {Type.int(4, False)}"
		func_str = "int32_t main(int32_t argc, char** argv, char** envp)"
		self.func.function_type = func_str
		self.func.view.update_analysis_and_wait()
		ft1 = self.func.function_type
		ft2 = self.bv.parse_type_string(func_str)[0]
		# ft2's calling convention is None and thus not expected to persist
		assert (ft1.return_value, ft1.parameters) == (ft2.return_value, ft2.parameters), f"{ft1} != {ft2}"

	def test_stack_layout(self):
		assert len(self.func.stack_layout) == 5
		assert len(self.func.core_var_stack_layout) == 5
		assert isinstance(self.func.stack_layout[0], Variable)
		assert isinstance(self.func.core_var_stack_layout[0], CoreVariable)

	def test_vars(self):
		assert len(self.func.vars) == 10
		assert len(self.func.core_vars) == 10
		assert isinstance(self.func.vars[0], Variable)
		assert isinstance(self.func.core_vars[0], CoreVariable)

	def test_indirect_branches(self):
		assert len(self.func.indirect_branches) == 0
		assert len(self.func.unresolved_indirect_branches) == 0
		assert not self.func.has_unresolved_indirect_branches

	def test_session_data(self):
		# TODO
		pass

	def test_analysis_performance_info(self):
		# TODO is there any better way to test this?
		assert isinstance(self.func.analysis_performance_info['Total'], float)

	def test_types(self):
		assert str(self.func.type_tokens[0]) == "int32_t"
		assert str(self.func.type_tokens[2]) == "main"

		assert self.func.return_type == Type.int(4, True)
		self.func.return_type = Type.void()
		self.bv.update_analysis_and_wait()
		assert self.func.return_type == Type.void()
		self.func.return_type = "uint64_t"
		self.bv.update_analysis_and_wait()
		assert self.func.return_type == Type.int(8, False)
		self.func.return_type = Type.int(4, True)
		self.bv.update_analysis_and_wait()
		assert self.func.return_type == Type.int(4, True)
		assert len(self.func.return_regs.regs) == 1
		assert self.func.return_regs.regs[0] == "r0"

		cc = self.func.calling_convention
		assert cc.name == 'cdecl'
		# clearing the calling convention makes analysis
		self.func.calling_convention = None
		self.bv.update_analysis_and_wait()
		assert self.func.calling_convention != None, f"{self.func.calling_convention} is None"
		self.func.calling_convention = cc
		self.bv.update_analysis_and_wait()
		assert self.func.calling_convention == cc
		self.func.mark_recent_use()

	def test_refs(self):
		from_addr = 0x0000843c
		to_addr = 0x00008440
		self.func.add_user_code_ref(from_addr, to_addr)
		refs = list(self.func.view.get_code_refs(from_addr))

	def test_reg_values(self):
		r0 = self.bv.arch.get_reg_index('r0')
		r3 = self.bv.arch.get_reg_index('r3')

		r3_after = self.func.get_reg_value_after(0x8474, r3);
		r0_after = self.func.get_reg_value_after(0x8478, r0);
		r3_at = self.func.get_reg_value_at(0x847c, r3);
		r0_at = self.func.get_reg_value_at(0x847c, r0);

		assert r0_after == r0_at
		assert r0_at == 0

		assert r3_after == r3_at
		assert r3_at == 0

	def test_pvs(self):
		func = self.func

		def first_var_by_name(name):
			return [v for v in func.vars if v.name == name][0]

		var_10 = first_var_by_name('var_10')
		r3 = first_var_by_name('r3')

		func.set_user_var_value(var_10, 0x8450, PossibleValueSet.constant_ptr(0x100))
		func.set_user_var_value(r3, 0x8454, PossibleValueSet.constant(0))

		all_vals = func.get_all_user_var_values()
		assert len(all_vals) == 2
		assert all_vals[var_10][ArchAndAddr(func.arch, 0x8450)] == PossibleValueSet.constant_ptr(0x100)
		assert all_vals[r3][ArchAndAddr(func.arch, 0x8454)] == PossibleValueSet.constant(0)

		func.clear_user_var_value(var_10, 0x8450)
		all_vals = func.get_all_user_var_values()
		assert len(all_vals) == 1

		func.set_user_var_value(var_10, 0x8450, PossibleValueSet.constant_ptr(0x100))
		all_vals = func.get_all_user_var_values()
		assert len(all_vals) == 2

		func.clear_all_user_var_values()
		all_vals = func.get_all_user_var_values()
		assert len(all_vals) == 0

	def test_auto_user(self):
		params = self.func.parameter_vars
		assert params[0].name == "argc"
		assert params[1].name == "argv"
		assert params[2].name == "envp"

		# Parameter variables
		new_params = params[0:2]
		self.func.set_auto_parameter_vars(new_params)
		self.bv.update_analysis()
		assert len(self.func.parameter_vars) == 2
		assert self.func.parameter_vars[0] == new_params[0]
		assert self.func.parameter_vars[1] == new_params[1]

		self.func.parameter_vars = [params[2]]
		self.bv.update_analysis_and_wait()
		assert len(self.func.parameter_vars) == 1
		assert self.func.parameter_vars[0] == params[2]

		# Can return
		self.func.set_auto_can_return(False)
		self.bv.update_analysis()
		assert self.func.can_return == False

		self.func.can_return = True
		self.bv.update_analysis_and_wait()
		assert self.func.can_return == True

		# Has variable arguments
		self.func.set_auto_has_variable_arguments(False)
		self.bv.update_analysis()
		assert self.func.has_variable_arguments == False

		self.func.has_variable_arguments = True
		self.bv.update_analysis_and_wait()
		assert self.func.has_variable_arguments == True

		# Stack adjustment
		self.func.set_auto_stack_adjustment(2)
		self.bv.update_analysis()
		assert self.func.stack_adjustment == 2

		self.func.stack_adjustment = 4
		self.bv.update_analysis_and_wait()
		assert self.func.stack_adjustment == 4

		# Return type
		rt = Type.int(2)
		rt2 = Type.int(4)
		self.func.set_auto_return_type(rt)
		assert self.func.return_type == rt
		self.func.return_type = rt2
		self.bv.update_analysis_and_wait()
		assert self.func.return_type == rt2

		# Indirect branches
		self.func.set_auto_indirect_branches(0x844c, [(self.func.arch, 0x842c)])
		assert len(self.func.indirect_branches) >= 1
		self.func.set_user_indirect_branches(0x844c, [(self.func.arch, 0x8428), (self.func.arch, 0x842c)])
		assert len(self.func.indirect_branches) >= 2

class TestBinaryView(TestWithBinaryView):
	def test_TagType(self):
		tt = self.bv.tag_types["Crashes"]
		t2 = self.bv.tag_types["Bugs"]
		assert repr(tt).startswith("<tag type Crashes: 🛑>")
		assert tt == tt
		assert tt != t2
		assert not (tt == t2)
		assert not (tt != tt)
		assert tt.__eq__(None) == NotImplemented
		assert tt.__ne__(None) == NotImplemented
		assert hash(tt) != hash(t2)
		assert len(tt.id) == len('796636ee-f2c3-4f67-a15e-20571fe37db2')
		assert tt.name == "Crashes"
		tt.name = "More Crashes"
		assert tt.name == "More Crashes"
		assert tt.icon == '🛑'
		tt.icon = '👀'
		assert tt.icon == '👀'
		assert tt.visible
		tt.visible = False
		assert not tt.visible
		assert tt.type == TagTypeType.UserTagType
		tt.type = TagTypeType.NotificationTagType
		assert tt.type == TagTypeType.NotificationTagType
		tt.type = TagTypeType.UserTagType
		assert tt.type == TagTypeType.UserTagType

	def test_Tag(self):
		func = self.bv.get_function_at(0x0000836c)
		assert len(func.address_tags) == 1
		arch, addr, tag = func.address_tags[0]
		assert repr(tag).startswith("<tag ")
		assert arch == func.arch
		assert addr == 0x00008390
		assert tag.data == 'Non-code call target 0x0'
		assert tag.type == self.bv.tag_types['Non-code Branch']
		func = self.bv.get_function_at(0x000083a4)
		assert len(func.address_tags) == 1
		_, _, other_tag = func.address_tags[0]
		assert tag == tag
		assert tag != other_tag
		assert tag.__eq__(None) == NotImplemented
		assert tag.__ne__(None) == NotImplemented
		assert hash(tag) != hash(other_tag)

	def test_log_api(self):
		bn.log.log_info("If this doesn't work then you `from .log import log` somewhere you shouldn't`")
		assert bn.log.is_output_redirected_to_log
		logger = bn.log.Logger(0, "test_logger")
		logger.log(LogLevel.DebugLog, "debug log")
		logger.log_info("log info")
		logger.log_debug("log debug")

	def test_sections(self):
		sections = self.bv.sections
		assert len(sections) == 25, f"section count is {len(sections)} not 25"
		section = sections['.ARM.exidx']
		section2 = sections['.bss']
		assert repr(section) == "<section .ARM.exidx: 0x851c-0x8524>"
		assert len(section) == 8
		assert section == section
		assert section != section2
		assert hash(section) != hash(section2)
		assert hash(section) == hash(section)
		assert section.start in section
		assert section.name == '.ARM.exidx'
		assert section.start == 0x851c
		assert section.linked_section == '.text'
		assert section.info_section == ''
		assert section.info_data == 0
		assert section.align == 4
		assert section.entry_size == 0
		assert section.semantics == SectionSemantics.ReadOnlyDataSectionSemantics
		assert section.auto_defined
		assert section.end == 0x8524
		assert section.type == ''

	def test_segments(self):
		segments = self.bv.segments
		segment = segments[0]
		assert len(segments) == 3
		assert len(segment) == 1320
		assert segment == segment
		assert segment != segments[1]
		assert segment.start in segment
		assert segment.start == 0x8000
		assert segment.end == 0x8528
		assert segment.readable
		assert not segment.writable
		assert segment.executable
		assert segment.data_length == 0x528
		assert segment.data_offset == 0x0
		assert segment.data_end == 0x8528
		assert segment.auto_defined
		assert segment.relocation_count == 0
		s2 = segments[1]
		assert s2.relocation_count == 5
		assert s2.relocation_ranges == [(69644, 69648), (69648, 69652), (69652, 69656), (69656, 69660), (69660, 69664)]
		assert s2.relocation_ranges_at(69644) == [(69644, 69648)]
		assert hash(segment) != hash(s2)

	def test_binary_data_nofification_default(self):
		bv = self.bv

		def simple_complete(self):
			results.append("analysis complete")
		event = bn.AnalysisCompletionEvent(bv, simple_complete)

		class NotifyTest(bn.BinaryDataNotification):
			pass

		test = NotifyTest()
		bv.register_notification(test)
		sacrificial_addr = 0x84fc

		type, name = bv.parse_type_string("int foo")
		type_id = Type.generate_auto_type_id("source", name)

		bv.define_type(type_id, name, type) # trigger type_defined
		bv.undefine_type(type_id) # trigger type_undefined
		bv.insert(sacrificial_addr, b"AAAA") # trigger data_inserted
		bv.define_data_var(sacrificial_addr, bn.types.Type.int(4)) # trigger data_var_added
		bv.write(sacrificial_addr, b"BBBB") # trigger data_written
		bv.add_function(sacrificial_addr) # trigger function_added
		bv.remove_function(bv.get_function_at(sacrificial_addr)) # trigger function_removed
		bv.undefine_data_var(sacrificial_addr) # trigger data_var_removed
		bv.remove(sacrificial_addr, 4) # trigger data_removed

		type, _ = bv.parse_type_string("struct { uint64_t bar; }")
		bv.define_user_type('foo', type)
		bv.define_user_type('bar', "struct { uint64_t bas; }")
		func = bv.get_function_at(0x8440)
		func.return_type = bn.Type.named_type_from_type('foo', type)
		func.name = "foobar" # trigger symbol_added
		func.name = "" # trigger symbol_removed

		msg1 = "Bugs here"
		name1 = "Bugs"
		tt1 = self.bv.tag_types[name1]
		tag1 = func.create_tag(tt1, msg1, True)

		assert len(func.function_tags) == 0
		func.add_user_function_tag(tag1)
		t = func.create_user_function_tag(tt1, msg1, True)
		tags = func.function_tags
		assert tags[0].data == msg1
		assert tags[0].type == tt1
		func.remove_user_function_tag(tags[0])

		bv.update_analysis_and_wait()
		bv.unregister_notification(test)

	def test_strings(self):
		string = self.bv.strings[0]
		assert repr(string) == '<AsciiString: 0x8154, len 0x12>', repr(string)
		assert string.value == '/lib/ld-linux.so.3'
		assert string.value == str(string)
		assert len(string) == 18
		assert isinstance(string.raw, bytes)
		assert string.type == StringType.AsciiString
		assert string.length == 18
		assert string.view.name == self.bv.name

	def test_analysis_info(self):
		ap = self.bv.analysis_progress
		assert str(ap) == "Idle"
		assert repr(ap) == "<progress: Idle>"

		ai = self.bv.analysis_info
		assert repr(ai) == "<AnalysisInfo 2, analysis_time 0, active_info []>"

	def test_symbolmapping(self):
		syms = self.bv.symbols
		assert repr(syms).startswith('<SymbolMapping ')
		assert next(self.bv.symbols)[0].name == "__elf_header"
		assert next(iter(self.bv.symbols)) == "__elf_header"
		assert "__elf_header" in syms
		for a in self.bv.symbols.keys():
			assert a == "__elf_header"
			break
		for a in self.bv.symbols.values():
			assert a[0].name == "__elf_header"
			break
		for a, b in self.bv.symbols.items():
			assert a == b[0].name
			break
		assert syms.get("__elf_header")[0].name == "__elf_header"
		assert syms.get("not_a_symbol", 0x41414141) == 0x41414141
		assert "foobar" not in syms

	def test_typemapping(self):
		tm = self.bv.types
		assert repr(tm).startswith("<TypeMapping")
		self.assertRaises(KeyError, lambda: tm["not a type"])
		self.assertRaises(KeyError, lambda: self.bv.types["not a type"])
		assert next(iter(tm))[0] == 'Elf32_Dyn'
		assert 'Elf32_Dyn' in self.bv.types
		assert 'asldkfjasd' not in self.bv.types
		assert tm == tm
		assert not (tm != tm)
		for a in self.bv.types.keys():
			assert a == "Elf32_Dyn"
			break
		for a in self.bv.types.values():
			assert a.registered_name.name == "Elf32_Dyn"
			break
		for a, b in self.bv.types.items():
			assert a == b.registered_name.name
			break
		assert tm.get("Elf32_Dyn").registered_name.name == "Elf32_Dyn"
		assert tm.get("not a type", 0x41414141) == 0x41414141

	def test_functionlist(self):
		bv = self.bv
		assert bv.functions[0] == bv.functions[0:1][0]
		self.assertRaises(IndexError, lambda: bv.functions[100000000])
		self.assertRaises(IndexError, lambda: bv.functions[0:100000000])
		self.assertRaises(ValueError, lambda: bv.functions["asdf"])


class TestBinaryViewType(unittest.TestCase):
	def test_binaryviewtype(self):
		self.assertRaises(KeyError, lambda: bn.BinaryViewType['not_a_binary_view'])
		bvt = BinaryViewType["PE"]
		bvt2 = BinaryViewType["ELF"]
		assert repr(bvt) == "<view type: 'PE'>"
		assert bvt == bvt
		assert bvt != bvt2
		assert hash(bvt) != hash(bvt2)
		assert bvt.name == "PE"
		assert bvt.long_name == "PE"
		assert not bvt.is_deprecated
		assert bvt2.get_arch(3, Endianness.LittleEndian) == Architecture["x86"]
		assert bvt2.get_platform(0, Architecture["x86"]) == Platform["linux-x86"]
		with FileApparatus("helloworld") as filename:
			with BinaryViewType.get_view_of_file(filename) as bv:
				assert bvt2.is_valid_for_data(bv.parent_view)
				assert isinstance(bvt2.parse(bv.parent_view), BinaryView)
		

