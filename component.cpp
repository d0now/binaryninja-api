
#include "binaryninjaapi.h"

using namespace BinaryNinja;
using namespace std;


Component::Component(BNComponent* type)
{
	m_object = type;
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


Ref<Component> Component::Create()
{
	BNComponent* component = BNComponentCreateEmpty();
	return new Component(component);
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
