#!/usr/bin/python
# -*- coding: utf-8 -*-
# quitbutton.py

import sys
from PyQt4 import QtGui, QtCore
import math

#class ZTerm():
#	def __init__(self):
#		name = ""
#		modalValue = 0
#		image = ""

class ZLinguisticVariable():
	""" Класс лингвистической переменной
	Описывает её имя, идентификатор (вида b2, s18 и т.п.),
	"""
	def __init__(self):
		self.name = ""	# человеческое название
		self.id = ""	# идентификатор вида b2, s18 и т.п.
		self.description = ""	# человеческое описание переменной
		self.terms = []	# термы переменной
		# степени принадлежности входного значения к термам
		self.degreesOfMembership = []

class ZRule():
	""" Класс правила вывода
	"""
	def __init__(self,source):
		self.source = source[:-1]
		self.conditions = []
		self.conclusions = []
	def calculate(self,linguisticVariableList):
		""" Определяет степень выполнения правила
		linguisticVariableList - список лингвистических
		переменных, содержащий степени принадлежности
		входных переменных термам

		возвращает список из двух элементов:
		result - значение левой стороны правила
		self.conclusions - список заключений, на которые влияет данное
		правило
		"""
		[leftPart, rightPart] = self.source.split(" => ")
		self.conditions = leftPart.split(" ")
		self.conclusions = rightPart.split(";")
		# Вычисление значения левой части
		# (обратная польская запись, стандартный алгоритм)
		stack = []
		for varOrOperator in self.conditions:
			if varOrOperator == "OR":
				operand1 = stack.pop()
				operand2 = stack.pop()
				stack.append(max(operand1,operand2))
			elif varOrOperator == "AND":
				operand1 = stack.pop()
				operand2 = stack.pop()
				stack.append(min(operand1,operand2))
			else:
				[varId,termId] = varOrOperator.split("-")
				for linguisticVariable in linguisticVariableList:
					if linguisticVariable.id.upper() == varId.upper():
                        # TODO защита от термов, выходящих за границы
						# массива
						index = int(termId)-1
						value = linguisticVariable.degreesOfMembership[0][index]
						stack.append(float(value))
						break
		# защита от пустого списка
		if stack:
			result = stack.pop()
		else:
			result=0.0
		return [result, self.conclusions]

class ZSlider(QtGui.QSlider):
	""" Класс слайдера выбора степеней принадлежности
	"""
	def __init__(self,parent=None):
		QtGui.QSlider.__init__(self,parent)
		self.setValue(0)

class ZWizardPage(QtGui.QWizardPage):
	""" Страница мастера
	При инициализации принимает объект ZLinguisticVariable
	использует его для заполнения формы
	"""
	def __init__(self,linguisticVariable,currentPage,totalPages,parent=None):
		QtGui.QWizardPage.__init__(self,parent)
		# определение заголовка
		self.setTitle(linguisticVariable.name + u"\n(страница "+str(currentPage+1)+u" из "+str(totalPages)+u")")
		groupBox = QtGui.QGroupBox(linguisticVariable.name)
		# текстовое поле с описанием переменной
		label = QtGui.QLabel(linguisticVariable.description)
		label.setWordWrap(True)
		# вертикальный лейаут для термов
		verticalLayout = QtGui.QVBoxLayout()
		# Наполнение лейаута названиями термов
		for term in linguisticVariable.terms:
			termLabel = QtGui.QLabel(term[0])
			termLabel.setWordWrap(True)
			verticalLayout.addWidget(termLabel)
			# перемежаем надписи разделителями
			verticalLayout.addStretch()
		# удалим нижний разделитель
		verticalLayoutLastItem = verticalLayout.itemAt(verticalLayout.count()-1)
		verticalLayout.removeItem(verticalLayoutLastItem)
		# слайдер
		self.slider = ZSlider(QtCore.Qt.Vertical)
		# пространство для отображения примеров почерка
		graphicsView = QtGui.QGraphicsView()
		# заполнение лейаутов
		horizontalLayout = QtGui.QHBoxLayout()
		horizontalLayout.addLayout(verticalLayout)
		horizontalLayout.addWidget(self.slider)
		horizontalLayout.addWidget(graphicsView)
		self.setLayout(horizontalLayout)

class ZReportWizardPage(QtGui.QWizardPage):
	def __init__(self,parent=None):
		QtGui.QWizardPage.__init__(self,parent)
		self.setTitle(u"Результат графологического анализа")
		self.label = QtGui.QLabel()
		self.label.setWordWrap(True)
		verticalLayout = QtGui.QVBoxLayout()
		verticalLayout.addWidget(self.label)
		self.setLayout(verticalLayout)

class ZReportDialog(QtGui.QDialog):
	def __init__(self,parent=None):
		QtGui.QDialog.__init__(self,parent)

class ZWizard(QtGui.QWizard):
	""" Класс мастера графанализа

	На основании входных списков переменных показывает пользователю
	ряд диалоговых форм для сбора информации о почерке.
	На основании списка правил анализирует их и представляет отчёт
	"""
	def __init__(self, parent=None):
		QtGui.QWizard.__init__(self,parent)
		self.linguisticVariableList = []
		self.readLinguisticVariables()
		self.setWizardStyle(QtGui.QWizard.ModernStyle)
		for linguisticVariableIndex in range(len(self.linguisticVariableList)):
			self.addPage(ZWizardPage(self.linguisticVariableList[linguisticVariableIndex],
				linguisticVariableIndex,len(self.linguisticVariableList)))
		self.lastPageId = self.addPage(ZReportWizardPage())
		self.setWindowTitle(u"Графологический анализ")
		self.connect(self, QtCore.SIGNAL("currentIdChanged(int)"), self.currentIdChanged)
		# TODO русификация кнопок

	def currentIdChanged(self,pageId):
		""" Слот, подготавливающий отчёт при переходе
		на последнюю страницу

		Выполняет анализ характеристик и выводи отчёт
		"""
		print pageId
		if pageId == self.lastPageId:
			self.saveDegreesOfMembership()
			conclusionNames = [	"C-","C+",
						"9-","9+",
						"3-","3+",
						"G-","G+",
						"M-","M+",
						"F-","F+"]
			resultList = [ 		0.0, 0.0,
						0.0, 0.0,
						0.0, 0.0,
						0.0, 0.0,
						0.0, 0.0,
						0.0, 0.0]
			ruleList = self.readRules()
			for rule in ruleList:
				[value, conclusionList] = rule.calculate(self.linguisticVariableList)
	#			print conclusionList
				for conclusion in conclusionList:
					#print conclusion
					index = conclusionNames.index(conclusion)
					newValue = resultList[index] + value
					resultList[index] =  newValue
			print conclusionNames
			print resultList
			humanReport = self.prepareHumanReport(resultList)
			self.page(self.lastPageId).label.setText(humanReport)

	def prepareHumanReport(self,resultList):
		conclusionHumanNames = [
u"""Эмоциональная устойчивость (С+)
Человек уравновешенный, хладнокровный, взвешенный, смотрит в лицо фактам, твердый, стабильный, сдержанный. Он реалистичен, способен следовать коллективной морали, обладает эмоциональной зрелостью.
""",u"""Эмоциональная неустойчивость (С-) 
Человек непостоянный, инфантильный, реактивный, обладает склонностью к уклонению от постоянного выполнения необходимых требований действительности и правил организации. Наблюдается низкая устойчивость по отношению к фрустрации, активно проявляется неудовольствие, суета и раздражительность. Известно, что низкая эмоцнональная устойчивость является наиболее общей составной частью всех патологических отклонений, неврозов, психопатий, алкоголизма и т.п.
""",u"""Демонстративность (3+)
Человек с ярко выраженными истерическими чертами, проявляющимися в эгоцентризме, стремлении к позерству, демонстративному поведению. повышенному стремлению обратить на себя внимание Каждый поступок, каждый жест, каждое движение рассчитаны на зрителя, на внешний эффект, все в них лживо и театрально. 
""",u"""Скромность (3-)
Человек замкнутый и недостаточно спонтанный в межличностных отношениях.
""",u"""Общительность (9+)
Для такого человека характерно приподнятое настроение независимо от обстоятельств. Он активен, деятелен, энергичен и жизнерадостен, но интересы его поверхностны и неустойчивы. Наблюдается любопытство, жажда деятельности, безрассудно смелая тяга к новому, к острым ощущениям. Это повышенная общительность, хорошо развитые навыки общения, широкие поверхностные контакты. Социальная адаптация без существенных затруднений. 
""",u"""Замкнутость (9-)
Человек склонен к невысокой активности, недостатку побуждений, низкой самооценке. Могут наблюдаться и признаки депрессии. Нет равновесия и уверенности в человеческих отношениях. В обществе такие люди легко тушуются, чувствуют скованность, нервничают, часто теряют душевное равновесие. Возможно, по этой причине они держатся холодно и отчужденно. Однако они не аффектированы в своей отчужденности, просто стараются соблюдать дистанцию, держатся в стороне, ничему не противясь, уважают права других и не навязывают своих собственных взглядов.
""",u"""Мечтательность (M+)
Человек склонен к мечтательности, фантазии, обладает богатым воображением. Часто погружен в себя, не обращает внимания на важные вещи и повседневные дела. Человеком могут игнорироваться общепринятые нормы и правила. Обладая творческим воображением, оторванным от конкретной действительности, он мало обращает внимания на окружающих людей и реальность. Из-за направленных на себя интересов часто попадает в необычные ситуации, проявляя в них сильные эмоциональные реакции, иногда неадекватные.
""",u"""Практичность (M-)
Человек практичный, прагматичный, ориентирован на внешнюю деятельность и следующий общепринятым нормам. Он внимателен к практически важным вещам, деталям, ориентируется на наиболее вероятное и не даёт волю своим эмоциям в неожиданных ситуациях, при этом ему может не хватать воображения.
""",u"""Беспечность (F+)
Человек импульсивный, беспечный, возбуждённый и экспрессивный. Таких нередко выбирают лидером, и они обладают быстрой реакцией на происходящее. Для них характерны искренность, подвижность и беззаботность.
""",u"""Озабоченность (F-)
Человек сдержан, рассудителен, благоразумен, серьезен. Он склонен к озабоченности, самонаблюдению и самоконтролю. Иногда он чрезмерно осторожен, пессимистичен, а окружающие могут считать его человеком с гонором. У него чаще замедленная реакция на события.
""",u"""Педантичность (G+ )
Человек склонен к педантичности, требовательности, аккуратности, добросовестности. Он руководствуется долгом, выполняет правила, соблюдает порядок, внимателен к людям, тверд, точен. Предпочитает работающих людей праздной компании.
""",u"""Несобранность (G-)
Человек склонен к непостоянству, поддается влиянию случая, не делает усилий по выполнению коллективных требований или приказаний, не соблюдает культурные нормы. Всегда стремится к выгоде, вольно трактует правила, что часто приводит к асоциальным последствиям и нарушениям.
""" ]
		report = u""
		for index in range(0, len(resultList), 2):
			valuePlus = resultList[index+1]
			valueMinus = resultList[index]
			if valuePlus+valueMinus >= 2:
				superiority = (valuePlus-valueMinus)/(valuePlus+valueMinus)
				if superiority >= 0.333:
					report += conclusionHumanNames[index+1]
					report += "\n"
				elif superiority <= -0.333:
					report += conclusionHumanNames[index]
					report += "\n"
		if report == u"":
			report = u"Психологические особенности не выявлены"
		else:
			report = u"В результате графологического анализа были выявлены следущие психологические особенности:\n\n" + report
		return report


	def readRules(self):
		""" Считывает из файла правила вывода
		и возвращяет заполненный ими список ruleList
		"""
		ruleFile=open("rules.txt","r")
		ruleList = []
		for line in ruleFile:
			if line[0].isalpha():
				rule = ZRule(line)
				ruleList.append(rule)
		ruleFile.close()
		return ruleList

	def readLinguisticVariables(self):
		""" Считывает из файла список лингвистических переменных
		сохраняет его в self.linguisticVariableList
		"""
		# Read variable file
		linguisticVariableFile = open("lv.txt","r")
		# TODO check file format
		for line in linguisticVariableFile:
			line = unicode(line, "UTF-8")
			# обрабатываются только строки, начинающиеся с цифры
			if(line[0].isdigit()):
				linguisticVariableTemp = line.split('	')
				termList = []
				# термы начинаются с этого места:
				for term in linguisticVariableTemp[4:]:
					term = term[1:-1]
					term = term.split(";")
					# наполним ими список термов
					termList.append(term)
				# запишем полученную информацию в объект класса ZLinguisticVariable
				linguisticVariable = ZLinguisticVariable()
				linguisticVariable.name = linguisticVariableTemp[1]
				linguisticVariable.id = linguisticVariableTemp[2]
				linguisticVariable.description = linguisticVariableTemp[3]
				linguisticVariable.terms = termList
				self.linguisticVariableList.append(linguisticVariable)
		linguisticVariableFile.close()

	def saveDegreesOfMembership(self):
		""" Сохраняет степени принадлежности в список класса
		self.linguisticVariableList
		"""
		for id in self.pageIds()[:-1]:
			value = self.page(id).slider.value()
			modalValues = [term[1]
					for term in self.linguisticVariableList[id].terms]
			degreesOfMembership = self.findDegreesOfMembership(value, modalValues)
			self.linguisticVariableList[id].degreesOfMembership.append(degreesOfMembership)

	def findDegreesOfMembership(self, x, modalValues):
		""" Находит степени принадлежности x к термам, заданным
		модальными значениями modalValues.

		Возвращает список степеней принадлежности для каждого терма
		"""
		# преобразуем элементы списка в float
		modalValues = [float(modalValue) for modalValue in modalValues]
		# создадим массив степеней принадлежности
		# элементов в нём должно быть столько же, сколько в modalValues
		output = [0.0 for item in modalValues]
		# флаг нахождения интервала
		isFound = False
		# ищем интервал слева и между модальных значений
		for modalValue in modalValues:
			if x < modalValue:
				isFound = True
				rightIndex = modalValues.index(modalValue)
				break
		# если нашли, то переменная либо..
		if isFound:
			# ..либо левее левого модального значения..
			if rightIndex == 0:
				output[0]=1.0
			# ..либо лежит между ними
			else:
				# в этом случае найдём степени принадлежности её к двум
				# термам, модальные значения которых окружают переменную
				leftIndex = rightIndex - 1
				modalValueRight = modalValues[rightIndex]
				modalValueLeft = modalValues[leftIndex]
				cosValue = 0.5*math.cos((x-modalValueRight)*math.pi/
						(modalValueRight-modalValueLeft))
				output[leftIndex] = 0.5 - cosValue
				output[rightIndex] = 0.5 + cosValue
		# если не нашли, что переменная лежит правее модальных значений
		else:
			output[len(output)-1] = 1.0
		# print output
		return output


app = QtGui.QApplication(sys.argv)
wizard = ZWizard()
wizard.show()
sys.exit(app.exec_())

