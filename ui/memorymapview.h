#pragma once

#include <QtWidgets/QAbstractScrollArea>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QTableWidget>

#include "dockhandler.h"
#include "render.h"
#include "sidebar.h"
#include "uitypes.h"
#include "fontsettings.h"


class BINARYNINJAUIAPI MemoryMapSidebarWidgetItem : public QTableWidgetItem
{
public:
	MemoryMapSidebarWidgetItem(const QString& text, int type=QTableWidgetItem::ItemType::Type): QTableWidgetItem(text, type) {};
	bool operator<(const QTableWidgetItem& other) const;
};


class BINARYNINJAUIAPI MemoryMapSidebarWidget : public SidebarWidget
{
	Q_OBJECT

	QTableWidget* m_table;
	QWidget* m_header;
	BinaryViewRef m_data;

	void updateInfo();

  public:
	MemoryMapSidebarWidget(ViewFrame* view, BinaryViewRef data);

	void notifyFontChanged() override { setFont(getMonospaceFont(this)); }
	QWidget* headerWidget() override { return m_header; }
};

class BINARYNINJAUIAPI MemoryMapSidebarWidgetType : public SidebarWidgetType
{
  public:
	MemoryMapSidebarWidgetType();
	SidebarWidget* createWidget(ViewFrame* frame, BinaryViewRef data) override;
};
