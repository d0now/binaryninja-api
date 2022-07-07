#pragma once

#include <QtWidgets/QAbstractScrollArea>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QTableWidget>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QPushButton>

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


class BINARYNINJAUIAPI SegmentDialog : public QDialog
{

	QPushButton* m_acceptButton;
	QPushButton* m_cancelButton;
	QLineEdit* m_startField;
	QLineEdit* m_lengthField;
	QLineEdit* m_dataOffsetField;
	QLineEdit* m_dataLengthField;
	QCheckBox* m_flagRead;
	QCheckBox* m_flagWrite;
	QCheckBox* m_flagExec;

	BinaryViewRef m_data;
	SegmentRef m_segment;

	void Submit();
public:
	SegmentDialog(QWidget* parent, BinaryViewRef data, SegmentRef segment = nullptr);
};


class BINARYNINJAUIAPI MemoryMapSidebarWidget : public SidebarWidget
{
	Q_OBJECT

	QTableWidget* m_sectionTable;
	QTableWidget* m_segmentTable;
	QWidget* m_header;
	BinaryViewRef m_data;

	void showSegmentContextMenu(const QPoint& point);
	void showSectionContextMenu(const QPoint& point);
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
