﻿#!/usr/bin/python
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
	def __init__(self):
		self.name = ""
		self.id = ""
		self.description = ""
		self.terms = []
		self.degreesOfMembership = []

class ZRule():
	def __init__(self,source):
		self.source = source[:-1]
		self.conditions = []
		self.conclusions = []
	def calculate(self,linguisticVariableList):
		[leftPart, rightPart] = self.source.split(" => ")
		self.conditions = leftPart.split(" ")
		self.conclusions = rightPart.split(";")
		#print self.conditions
		#print type(self.conditions)
		# Вычисление значения левой части (обратная польская запись)
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
                        # TODO защита от термов, выходящих за границы массива
						stack.append(float(linguisticVariable.degreesOfMembership[0][int(termId)-1]))
						break
			#print stack
		if stack:
			result = stack.pop()
		else:
			result=0.0
		return [result, self.conclusions]




class ZSlider(QtGui.QSlider):
	def __init__(self,parent=None):
		QtGui.QSlider.__init__(self,parent)
		self.setValue(0)

class ZWizardPage(QtGui.QWizardPage):
	def __init__(self,linguisticVariable,parent=None):
		QtGui.QWizardPage.__init__(self,parent)
		self.setTitle(linguisticVariable.name)
		label = QtGui.QLabel(linguisticVariable.description)

		label.setWordWrap(True)
		layout = QtGui.QVBoxLayout()
		self.slider = ZSlider(QtCore.Qt.Vertical)
		layout.addWidget(label)
		layout.addWidget(self.slider)
		self.setLayout(layout)

class ZWizard(QtGui.QWizard):
	def __init__(self, parent=None):
		QtGui.QWizard.__init__(self,parent)
		self.linguisticVariableList = []
		self.readLinguisticVariables()
#		self.setWizardStyle(QtGui.QWizard.ModernStyle)
		for linguisticVariable in self.linguisticVariableList:
			self.addPage(ZWizardPage(linguisticVariable))
		self.setWindowTitle(u"Графологический анализ")

	def accept(self):
		self.saveDegreesOfMembership()
		conclusionNames = ["C-","C+","9-","9+","3-","3+","G-","G+","M-","M+","F-","F+"]
		resultList = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
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
		QtGui.QDialog.accept(self)

	def readRules(self):
		ruleFile=open("rules.txt","r")
		ruleList = []
		for line in ruleFile:
			if line[0].isalpha():
				rule = ZRule(line)
				ruleList.append(rule)
		ruleFile.close()
		return ruleList

	def readLinguisticVariables(self):
		# Read variable file
		linguisticVariableFile = open("lv.txt","r")
		# TODO check file format
		for line in linguisticVariableFile:
			line = unicode(line, "UTF-8")
			if(line[0].isdigit()):
				linguisticVariableTemp = line.split('	')
				termList = []
				for term in linguisticVariableTemp[4:]:
					term = term[1:-1]
					term = term.split(";")
					termList.append(term)
				#linguisticVariable = linguisticVariable[:3]+termList
				linguisticVariable = ZLinguisticVariable()
				linguisticVariable.name = linguisticVariableTemp[1]
				linguisticVariable.id = linguisticVariableTemp[2]
				linguisticVariable.description = linguisticVariableTemp[3]
				linguisticVariable.terms = termList
				self.linguisticVariableList.append(linguisticVariable)
		linguisticVariableFile.close()

	def saveDegreesOfMembership(self):
		for id in self.pageIds():
			value = self.page(id).slider.value()
			modalValues = [term[1] for term in self.linguisticVariableList[id].terms]
			degreesOfMembership = self.findDegreesOfMembership(value, modalValues)
			self.linguisticVariableList[id].degreesOfMembership.append(degreesOfMembership)

	def findDegreesOfMembership(self, x, modalValues):
		modalValues = [float(modalValue) for modalValue in modalValues]
		output = [0.0 for item in modalValues]
		isFound = False
		for modalValue in modalValues:
			if x < modalValue:
				isFound = True
				rightIndex = modalValues.index(modalValue)
				break
		if isFound:
			if rightIndex == 0:
				output[0]=1.0
			else:
				leftIndex = rightIndex - 1
				modalValueRight = modalValues[rightIndex]
				modalValueLeft = modalValues[leftIndex]
				output[leftIndex] = 0.5 - 0.5*math.cos((x-modalValueRight)*math.pi/(modalValueRight-modalValueLeft))
				output[rightIndex] = 0.5 + 0.5*math.cos((x-modalValueRight)*math.pi/(modalValueRight-modalValueLeft))
		else:
			output[len(output)-1] = 1.0
		# print output
		return output


app = QtGui.QApplication(sys.argv)
wizard = ZWizard()
wizard.show()
sys.exit(app.exec_())

