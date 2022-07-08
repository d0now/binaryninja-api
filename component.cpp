
#include "binaryninjaapi.h"

using namespace BinaryNinja;
using namespace std;


/*
#include <string>

#include "binaryninjaapi.h"
#include "gtest/gtest.h"
#include <stdio.h>
#include <unistd.h>

using namespace BinaryNinja;
using namespace std;

#define ASSERT_VECTOR_CONTAINS(vector, item) ASSERT_TRUE(std::find(vector.begin(), vector.end(), item) != vector.end())
#define ASSERT_NOT_VECTOR_CONTAINS(vector, item) ASSERT_FALSE(std::find(vector.begin(), vector.end(), item) != vector.end())
#define ASSERT_VECTOR_EMPTY(vector) ASSERT_EQ(vector.size(), 0)
#define ASSERT_VECTOR_NOT_EMPTY(vector) ASSERT_TRUE(vector.size() != 0)

TEST(API_Components, ComponentTests)
{
	Ref<BinaryData> data = new BinaryData(new FileMetadata(), "/Volumes/Secure/test_components/binaryninja/api/suite/binaries/test_corpus/helloworld");

	Ref<BinaryView> bv;
	for (auto type : BinaryViewType::GetViewTypes())
	{
		if (type->IsTypeValidForData(data) && type->GetName() != "Raw")
		{
			bv = type->Create(data);
			break;
		}
	}

	if (!bv || bv->GetTypeName() == "Raw")
	{
		fprintf(stderr, "Input file does not appear to be an exectuable\n");
		return;
	}

	bv->UpdateAnalysisAndWait();

	Ref<Component> component = new Component();

	Ref<Function> function = bv->GetAnalysisEntryPoint();

	auto functions = component->GetContainedFunctions();
	ASSERT_NOT_VECTOR_CONTAINS(functions, function);
	ASSERT_TRUE(component->AddFunction(function));
	functions = component->GetContainedFunctions();
	ASSERT_VECTOR_CONTAINS(functions, function);

	ASSERT_VECTOR_NOT_EMPTY(component->GetReferencedTypes());
	ASSERT_VECTOR_NOT_EMPTY(component->GetReferencedDataVariables());

	ASSERT_TRUE(component->RemoveFunction(function));
	functions = component->GetContainedFunctions();
	ASSERT_NOT_VECTOR_CONTAINS(functions, function);
	ASSERT_VECTOR_EMPTY(functions);
	ASSERT_VECTOR_EMPTY(component->GetReferencedTypes());
	ASSERT_VECTOR_EMPTY(component->GetReferencedDataVariables());

	auto components = component->GetContainedComponents();
	Ref<Component> newComponent = new Component();
	ASSERT_NOT_VECTOR_CONTAINS(components, newComponent);
	ASSERT_TRUE(component->AddComponent(newComponent));
	components = component->GetContainedComponents();
	ASSERT_VECTOR_CONTAINS(components, newComponent);
	ASSERT_TRUE(component->RemoveComponent(newComponent));
	components = component->GetContainedComponents();
	ASSERT_NOT_VECTOR_CONTAINS(components, newComponent);
	ASSERT_VECTOR_EMPTY(components);

	component->SetName("TestName1");
	ASSERT_STREQ(component->GetName().c_str(), "TestName1");

	ASSERT_TRUE(bv->AddComponent(component));

	auto c = bv->GetComponentByGUID(component->GetGUID());
	ASSERT_TRUE(c.has_value());

	ASSERT_TRUE(bv->RemoveComponent(c.value()));
	c = bv->GetComponentByGUID(component->GetGUID());
	ASSERT_FALSE(c.has_value());
	ASSERT_EQ(bv->GetComponents().size(), 0); // This fails.

	ASSERT_TRUE(bv->AddComponent(component));
	c = bv->GetComponentByGUID(component->GetGUID());
	ASSERT_TRUE(c.has_value());

	bv->RemoveComponentByGUID(c.value()->GetGUID());
	c = bv->GetComponentByGUID(component->GetGUID());
	ASSERT_FALSE(c.has_value());

}
 * */


Component::Component()
{
	m_object = BNComponentCreateEmpty();
}


Component::Component(BNComponent* component)
{
	m_object = component;
}


std::string Component::GetName()
{
	return BNComponentGetName(m_object);
}


void Component::SetName(const std::string &name)
{
	BNComponentSetName(m_object, name.c_str());
}


Ref<Component> Component::GetParent()
{
	return new Component(BNComponentGetParent(m_object));
}


std::string Component::GetGUID()
{
	return string(BNComponentGetGUID(m_object));
}


bool Component::AddFunction(Ref<Function> func)
{
	return BNComponentAddFunctionReference(m_object, func->GetObject(), true);
}


bool Component::RemoveFunction(Ref<Function> func)
{
	return BNComponentRemoveFunctionReference(m_object, func->GetObject(), true);
}


bool Component::AddComponent(Ref<Component> component)
{
	return BNComponentAddComponentReference(m_object, component->GetObject());
}


bool Component::RemoveComponent(Ref<Component> component)
{
	return BNComponentRemoveComponentReference(m_object, component->GetObject());
}


std::vector<Ref<Component>> Component::GetContainedComponents()
{
	std::vector<Ref<Component>> components;

	size_t count;
	BNComponent** list = BNComponentGetContainedComponents(m_object, &count);

	components.reserve(count);
	for (size_t i = 0; i < count; i++)
	{
		Ref<Component> component = new Component(list[i]);
		components.push_back(component);
	}

	return components;
}


std::vector<Ref<Function>> Component::GetContainedFunctions()
{
	std::vector<Ref<Function>> functions;

	size_t count;
	BNFunction** list = BNComponentGetContainedFunctions(m_object, &count);

	functions.reserve(count);
	for (size_t i = 0; i < count; i++)
	{
		Ref<Function> function = new Function(list[i]);
		functions.push_back(function);
	}

	return functions;
}


std::vector<Ref<Type>> Component::GetReferencedTypes()
{
	std::vector<Ref<Type>> types;

	size_t count;
	BNType** list = BNComponentGetReferencedTypes(m_object, &count);

	types.reserve(count);
	for (size_t i = 0; i < count; i++)
	{
		Ref<Type> type = new Type(list[i]);
		types.push_back(type);
	}

	return types;
}


std::vector<DataVariable> Component::GetReferencedDataVariables()
{
	vector<DataVariable> result;

	size_t count;
	BNDataVariable* variables = BNComponentGetReferencedDataVariables(m_object, &count);

	result.reserve(count);
	for (size_t i = 0; i < count; ++i)
	{
		result.emplace_back(variables[i].address,
			Confidence(new Type(BNNewTypeReference(variables[i].type)), variables[i].typeConfidence),
			variables[i].autoDiscovered);
	}

	BNFreeDataVariables(variables, count);
	return result;
}
