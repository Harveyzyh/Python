from SqlHelper import MsSqlHelper
from BaseHelper import Logger
import sys
from time import sleep


class AutoErpPlanHelper:
	def __init__(self, debug=False, logger=Logger(sys.path[0] + '/Log/AutoErpPlan.log'), host='192.168.0.99'):
		self.__logger = logger
		self.__debugMode = debug
		self.__host = host

		self.__mssql = None

		self.workingFlag = False

	def __log(self, string, mode='info'):
		if mode == 'info':
			self.__logger.logger.info('AutoErpPlan: {}'.format(string))
		elif mode == 'error':
			self.__logger.logger.error('AutoErpPlan: {}'.format(string))
		elif mode == 'warning':
			self.__logger.logger.warning('AutoErpPlan: {}'.format(string))

	def __del(self):
		del self.__mssql
		self.__mssql = None

	def __str_to_hex(self, s):
		# return '00'.join([hex(ord(c)).replace('0x', '') for c in s]).upper()
		returnStr = ''
		for c in s:
			strTmp = hex(ord(c)).replace('0x', '').upper()
			if len(strTmp) == 2:
				strTmp2 = strTmp + '00'
			else:
				strTmp2 = strTmp[2:4] + strTmp[0:2]
			returnStr += strTmp2
		return returnStr

	def __int_to_hex(self, i):
		# return str(hex(i)).replace('0x', '').rjust(2, '0').upper()
		returnStr = ''
		strTmp = str(hex(i)).replace('0x', '').rjust(2, '0').upper()
		if len(strTmp) == 2:
			strTmp2 = strTmp + '00'
		else:
			strTmp2 = strTmp[2:4] + strTmp[0:2]
		returnStr += strTmp2
		return returnStr

	def work(self, mode='title'):
		try:
			self.__log('Work Start')
			self.workingFlag = True

			self.__mssql = MsSqlHelper(host=self.__host, user='sa', passwd='comfortgroup2016{', database='COMFORT')

			self.__work()

		except Exception as e:
			self.__log(str(e), mode='error')

		finally:
			self.workingFlag = False
			self.__del()
			self.__log('Work Finished')

	def test(self):
		# self.__mssql = MsSqlHelper(host=self.__host, user='sa', passwd='comfortgroup2016{', database='COMFORT')
		# self.__lockPlan(planId='A2201000001')
		print('Do Nothing')

	def __work(self):
		__sqlStrDd = "SELECT DISTINCT TC001+'-'+RTRIM(TC002) planDd, 'A'+TC001+RTRIM(TC002) planId, TC003 " \
		             "FROM COMFORT.dbo.COPTC " \
		             "INNER JOIN COMFORT.dbo.COPTD ON TD001 = TC001 AND TD002 = TC002 " \
		             "WHERE 1=1 " \
		             "AND COPTC.TC027 = 'Y' " \
		             "AND NOT EXISTS(SELECT 1 FROM  COMFORT.dbo.MOCTA " \
		             "    WHERE TA026 = TD001 AND TA027 = TD002 AND TD028 = TD003 ) " \
		             "AND NOT EXISTS(SELECT 1 FROM  COMFORT.dbo.LRPLB " \
		             "    WHERE LB002 = TD001 AND LB003 = TD002 AND LB004 = TD003 ) " \
		             "AND COPTC.LRPFLAG = 'N' " \
		             "AND COPTC.TC003 >= '20200401' " \
		             "AND COPTC.TC001 NOT IN ('2215', '2216', '2217') " \
		             "ORDER BY TC003, TC001+'-'+RTRIM(TC002) "

		__getDd = self.__mssql.sqlWork(__sqlStrDd)
		if __getDd is not None:
			for __getDdTmp in __getDd:
				self.__log('Work With PlanDd:{planDd}  PlanId:{planId}'.format(planDd=__getDdTmp[0],
				                                                               planId=__getDdTmp[1]))
				__phList = self.__getPhList(__getDdTmp[0])
				self.__calculate(__phList)
				self.__generate(planDd=__getDdTmp[0], planId=__getDdTmp[1])
				self.__lockPlan(planId=__getDdTmp[1])
				self.__updateFlagTitle(planDd=__getDdTmp[0])
		else:
			self.__log('Not Found Order List!')

	def __getPhList(self, dd):
		__sqlStr = "SELECT DISTINCT RTRIM(TD004) FROM COMFORT.dbo.COPTD WHERE TD001+'-'+RTRIM(TD002) = '{dd}' "
		__get = self.__mssql.sqlWork(__sqlStr.format(dd=dd))
		__rtnList = None
		if __get is not None:
			__rtnList = []
			[__rtnList.append(str(__get[index][0])) for index in range(len(__get))]
		return __rtnList

	def __calculate(self, phList=None):
		if phList is not None:
			self.__log('Calculate PhList: {}'.format(phList))
			for phListTmp in phList:
				jobId = self.__bomCalculate(phListTmp)
				self.__checkJobDone(jobId)
				jobId = self.__pzCalculate(phListTmp)
				self.__checkJobDone(jobId)
		else:
			self.__log('Calculate: Not Found PhList!', mode='warning')

	def __bomCalculate(self, ph):
		__sqlStrIns = "INSERT INTO DSCSYS.dbo.JOBQUEUE ([JOBID], [SUBID], [COMPANYID], [USERID], [USEDALIAS], [JOBNAME], " \
		              "[EXTNAME], [COMPROGID], [JOBOPTION], [GENTYPE], [GENSTATUS], [PRIORITY], [STATUS], [PROGRESS], " \
		              "[DTREQUEST], [DTRECEIVE], [DTSCHEDULE], [DTSTART], [DTFINISH], [RESULT], [STYLE], [PROCESSER], " \
		              "[FLAG], [NOTIFY]) " \
		              "VALUES ('{jobId}', '{subId}', 'COMFORT', 'Robot', 'COMFORT', 'BOMB05 ', '', " \
		              "'BOMB05S.Class1', {hexStr}, 1, 1, 3, 'N', NULL, getdate(), getdate(), getdate(), " \
		              "NULL, NULL, NULL, 'B', '', 1, '');"

		__hexStr = "0x44532056415249414E54202030313030380100000C2000000100000000000000010000000C2000000100000001000000" \
		           "030000000C20000001000000000000000100000008000000060000000990E9623B4EF64EC154F753080000000400000073" \
		           "007000300031000C20000001000000000000000100000008000000070000001F7510624C006F0067008765636808000000" \
		           "06000000630068006B004C006F0067000C20000001000000000000000100000008000000040000005C4F1A4EE5651F6708" \
		           "0000000B000000650064005000720069006E00740044006100740065000C2000000100000001000000030000000C200000" \
		           "0100000000000000020000000800000001000000040008000000{phLen}0000{ph}08000000{phLen}0000{ph}08000000" \
		           "010000004E000800000000000000"
		__jobId = self.__getJobId()
		phStr = self.__str_to_hex(ph)
		phLenStr = self.__int_to_hex(len(ph))
		self.__mssql.sqlWork(__sqlStrIns.format(hexStr=__hexStr.format(ph=phStr, phLen=phLenStr),
		                                        jobId=__jobId[0], subId=__jobId[1]))
		self.__log('Insert Job BomCalculate: {}'.format('品号:' + str(ph) + ' - JobId:' + str(__jobId[0])))
		return __jobId[0]

	def __pzCalculate(self, ph0):
		__sqlStrIns = "INSERT INTO DSCSYS.dbo.JOBQUEUE ([JOBID], [SUBID], [COMPANYID], [USERID], [USEDALIAS], [JOBNAME], " \
		              "[EXTNAME], [COMPROGID], [JOBOPTION], [GENTYPE], [GENSTATUS], [PRIORITY], [STATUS], [PROGRESS], " \
		              "[DTREQUEST], [DTRECEIVE], [DTSCHEDULE], [DTSTART], [DTFINISH], [RESULT], [STYLE], [PROCESSER], " \
		              "[FLAG], [NOTIFY]) " \
		              "VALUES ('{jobId}', '{subId}', 'COMFORT', 'Robot', 'COMFORT', 'COPAB02 ', '', " \
		              "'COPAB02S.Class1', {hexStr}, 1, 1, 3, 'N', NULL, getdate(), getdate(), getdate(), " \
		              "NULL, NULL, NULL, 'B', '', 1, '');"

		__sqlStrFind = "SELECT RTRIM(MB001), RTRIM(MB002), RTRIM(MB003), RTRIM(MB004) " \
		               "FROM COMFORT.dbo.INVMB WHERE MB001 = '{ph}' "

		ph, pm, gg, dw = self.__mssql.sqlWork(__sqlStrFind.format(ph=str(ph0)))[0]
		phStr = self.__str_to_hex(ph)
		phLenStr = self.__int_to_hex(len(ph))
		pmStr = self.__str_to_hex(pm)
		pmLenStr = self.__int_to_hex(len(pm))
		ggStr = self.__str_to_hex(gg)
		ggLenStr = self.__int_to_hex(len(gg))
		dwStr = self.__str_to_hex(dw)
		dwLenStr = self.__int_to_hex(len(dw))

		__hexStr = "0x44532056415249414E54202030313030CA0100000C2000000100000000000000010000000C2000000100000001000000" \
		           "040000000C20000001000000000000000100000008000000040000000990E962C154F75308000000040000007300700030" \
		           "0031000C20000001000000000000000100000008000000070000000990E96242004F004D00E5651F670800000004000000" \
		           "73007000300032000C20000001000000000000000100000008000000070000001F7510624C006F00670087656368080000" \
		           "0006000000630068006B004C006F0067000C20000001000000000000000100000008000000040000005C4F1A4EE5651F67" \
		           "080000000B000000650064005000720069006E00740044006100740065000C2000000100000001000000040000000C2000" \
		           "00010000000000000001000000080000000100000005000C20000001000000000000000300000008000000{phLen}0000" \
		           "{ph}08000000{pmLen}0000{pm}08000000{ggLen}0000{gg}08000000{dwLen}0000{dw}0C20000001000000000000000" \
		           "20000000800000001000000040008000000000000000800000000000000080000000100000059000800000000000000"

		__jobId = self.__getJobId()

		self.__mssql.sqlWork(__sqlStrIns.format(hexStr=__hexStr.format(ph=phStr, phLen=phLenStr, pm=pmStr,
		                                                               pmLen=pmLenStr, gg=ggStr, ggLen=ggLenStr,
		                                                               dw=dwStr, dwLen=dwLenStr),
		                                        jobId=__jobId[0], subId=__jobId[1]))

		self.__log('Insert Job PzCalculate: {}'.format('品号:' + str(ph) + ' - JobId:' + str(__jobId[0])))

		return __jobId[0]

	def __getJobId(self):
		__sqlStr = "EXEC COMFORT.dbo.P_GETJOBID "
		__getData = self.__mssql.sqlWork(__sqlStr)
		if __getData is not None:
			return __getData[0]
		else:
			return None

	def __checkJobDone(self, jobId):
		__sqlStr = "SELECT JOBID FROM DSCSYS.dbo.JOBQUEUE WHERE JOBID = '{jobId}' AND STATUS != 'D' "
		__getData = []
		while __getData is not None:
			sleep(0.5)
			__getData = self.__mssql.sqlWork(__sqlStr.format(jobId=jobId))
		self.__log('Job Done: {}'.format('JobId:' + str(jobId)))

	def __generate(self, planDd, planId):
		__jobId = self.__generatePlanTitle(planId=planId, planDd=planDd)
		self.__checkJobDone(__jobId)

	def __generatePlanTitle(self, planDd, planId):
		__sqlStrIns = "INSERT INTO DSCSYS.dbo.JOBQUEUE ([JOBID], [SUBID], [COMPANYID], [USERID], [USEDALIAS], [JOBNAME], " \
		              "[EXTNAME], [COMPROGID], [JOBOPTION], [GENTYPE], [GENSTATUS], [PRIORITY], [STATUS], [PROGRESS], " \
		              "[DTREQUEST], [DTRECEIVE], [DTSCHEDULE], [DTSTART], [DTFINISH], [RESULT], [STYLE], [PROCESSER], " \
		              "[FLAG], [NOTIFY]) " \
		              "VALUES ('{jobId}', '{subId}', 'COMFORT', 'Robot', 'COMFORT', 'LRPMB01', '', " \
		              "'LRPMB01S.Class1', {hexStr}, 1, 1, 3, 'N', NULL, getdate(), getdate(), getdate(), " \
		              "NULL, NULL, NULL, 'B', '', 1, '');"

		hexStrBoth = "0x44532056415249414E54202030313030C00700000C2000000100000000000000010000000C20000001000000010000" \
		             "00180000000C20000001000000000000000100000008000000060000000990E962A18B12529D4F6E6308000000050000" \
		             "00630062006F00300031000C20000001000000000000000100000008000000040000000990E962E55D82530800000004" \
		             "00000065006400300032000C20000001000000000000000100000008000000060000000990E9626567906E167FF75308" \
		             "0000000400000073007000300033000C2000000100000000000000010000000800000006000000938F6551A18B125279" \
		             "62F75308000000050000006D0065006400300034000C20000001000000000000000100000008000000040000000990E9" \
		             "62D34E935E080000000400000073007000300035000C20000001000000000000000100000008000000060000000990E9" \
		             "626588278D3F65567B0800000005000000630062006F00300036000C2000000100000000000000010000000800000006" \
		             "0000000097426CA18B977BB9650F5F0800000005000000720064006700300037000C2000000100000000000000010000" \
		             "00080000000600000003805186895B6851585BCF910800000005000000630068006B00300038000C2000000100000000" \
		             "00000001000000080000000C0000000097426CE5651F670E5484769B4FD97EB37E6551A18B977B080000000600000063" \
		             "0068006B003000380031000C200000010000000000000001000000080000000C0000000097426CE5651F670E54847600" \
		             "97426CB37E6551A18B977B0800000006000000630068006B003000380032000C20000001000000000000000100000008" \
		             "000000080000000990E96200971F7510628476A18B12520800000005000000630062006F00300039000C200000010000" \
		             "000000000001000000080000000C000000F95B8E4EF25DD1533E659965F64E847665884551B9650F5F08000000050000" \
		             "00630062006F00310030000C20000001000000000000000100000008000000090000001F7510620097426C3A4EF69684" \
		             "769965F64E0800000005000000630068006B00310031000C2000000100000000000000010000000800000008000000D6" \
		             "53FF66E34E9965B37E6551A18B977B0800000005000000630068006B00310032000C2000000100000000000000010000" \
		             "000800000008000000A25B37629B4F9965B37E6551A18B977B0800000007000000630068006B00300037005F0031000C" \
		             "200000010000000000000001000000080000000B0000000990E9624D0050005300A18B1252005FE55DE5651F67080000" \
		             "000400000073007000310036000C2000000100000000000000010000000800000005000000038051865F631780877308" \
		             "00000005000000630068006B00310033000C2000000100000000000000010000000800000005000000A18B977B5D4E27" \
		             "59CF910800000005000000630068006B00300039000C2000000100000000000000010000000800000008000000085476" \
		             "5EA18B977B00674E4F6588CF910800000005000000630068006B00310034000C20000001000000000000000100000008" \
		             "000000070000004151B88BF76D7962D653FF66E34E0800000005000000630068006B00310035000C2000000100000000" \
		             "00000001000000080000000200000048722C67080000000400000065006400310036000C200000010000000000000001" \
		             "00000008000000020000002760288D0800000005000000630062006F00310037000C2000000100000000000000010000" \
		             "0008000000070000001F7510624C006F006700876563680800000006000000630068006B004C006F0067000C20000001" \
		             "000000000000000100000008000000040000005C4F1A4EE5651F67080000000B000000650064005000720069006E0074" \
		             "0044006100740065000C2000000100000001000000180000000C20000001000000000000000100000003000000010000" \
		             "00080000000400000031002E00A28B55530800000002000000300031000C200000010000000000000001000000080000" \
		             "000100000005000C20000001000000000000000000000008000000{planDdLen}0000{planDd}08000000{planIdLen}" \
		             "0000{planId}0C200000010000000000000000000000080000000100000005000C200000010000000000000001000000" \
		             "08000000010000004C0008000000080000004C002E0009634C00520050000097426C0C20000001000000000000000100" \
		             "000003000000020000000800000003000000DB6B0097426C0800000001000000590008000000010000004E0008000000" \
		             "010000004E000C2000000100000000000000010000000300000003000000080000000400000033002E006851E8900C20" \
		             "00000100000000000000010000000300000002000000080000000600000032002E00CD91B06565884551080000000100" \
		             "00004E0008000000010000004E0008000000010000004E000C2000000100000000000000020000000800000001000000" \
		             "04000800000000000000080000000000000008000000010000004E0008000000010000004E0008000000010000004E00" \
		             "08000000010000004E00080000000400000030003000300031000C200000010000000000000001000000030000000100" \
		             "0000080000000400000031002E000967486508000000010000004E000800000000000000"

		planDdStr = self.__str_to_hex(str(planDd))
		planDdLenStr = self.__int_to_hex(len(str(planDd)))
		planIdStr = self.__str_to_hex(str(planId))
		planIdLenStr = self.__int_to_hex(len(str(planId)))

		__jobId = self.__getJobId()

		self.__mssql.sqlWork(__sqlStrIns.format(hexStr=hexStrBoth.format(planDd=planDdStr,
		                                                                 planDdLen=planDdLenStr,
		                                                                 planId=planIdStr,
		                                                                 planIdLen=planIdLenStr),
		                                        jobId=__jobId[0], subId=__jobId[1]))

		self.__log('Insert Job Generate Plan: {}'.format(str(planDd)))
		return __jobId[0]

	def __lockPlan(self, planId, planVer='0001'):
		planId2 = planId.ljust(20, ' ')
		__jobId = self.__lockScPlan(planId=planId2, planVer=planVer)
		self.__checkJobDone(__jobId)
		__jobId = self.__lockCgPlan(planId=planId2, planVer=planVer)
		self.__checkJobDone(__jobId)
		self.__log('Lock Plan Job Done: PlanId: {}'.format(planId))

	def __lockScPlan(self, planId, planVer):
		__sqlStrIns = "INSERT INTO DSCSYS.dbo.JOBQUEUE ([JOBID], [SUBID], [COMPANYID], [USERID], [USEDALIAS], [JOBNAME], " \
		              "[EXTNAME], [COMPROGID], [JOBOPTION], [GENTYPE], [GENSTATUS], [PRIORITY], [STATUS], [PROGRESS], " \
		              "[DTREQUEST], [DTRECEIVE], [DTSCHEDULE], [DTSTART], [DTFINISH], [RESULT], [STYLE], [PROCESSER], " \
		              "[FLAG], [NOTIFY]) " \
		              "VALUES ('{jobId}', '{subId}', 'COMFORT', 'Robot', 'COMFORT', 'LRPB02 ', '', " \
		              "'LRPB02S.Class1', {hexStr}, 1, 1, 3, 'N', NULL, getdate(), getdate(), getdate(), " \
		              "NULL, NULL, NULL, 'B', '', 1, '');"

		hexStr = "0x44532056415249414E54202030313030AE0400000C2000000100000000000000010000000C20000001000000010000000E" \
		         "0000000C20000001000000000000000100000008000000040000000990E962C154F753080000000400000073007000300031" \
		         "000C20000001000000000000000100000008000000040000000990E962E55D8253080000000400000065006400300032000C" \
		         "20000001000000000000000100000008000000040000000990E962D34E935E080000000400000073007000300033000C2000" \
		         "0001000000000000000100000008000000050000000990E9628C5BE55DE565080000000400000073007000300034000C2000" \
		         "0001000000000000000100000008000000060000000990E962A18B12527962F753080000000400000073007000300035000C" \
		         "20000001000000000000000100000008000000060000000990E962E55D555355532B52080000000400000065006400300036" \
		         "000C20000001000000000000000100000008000000060000000990E962A18B1252BA4E585408000000040000006500640030" \
		         "0037000C20000001000000000000000100000008000000060000000990E96201959A5BB67201600800000005000000720064" \
		         "006700300038000C200000010000000000000001000000080000000B000000C54E8894F95BC6620652B08B555FDB8F4C8801" \
		         "959A5B0800000005000000630068006B00300039000C200000010000000000000001000000080000000B000000C54E8894F9" \
		         "5BC6620652B08B555FD653886D01959A5B0800000005000000630068006B00310030000C2000000100000000000000010000" \
		         "0008000000070000000C54656B01959A5BA74E1062C1540800000005000000630068006B00310031000C2000000100000000" \
		         "0000000100000008000000090000000C54656BD653886D01959A5BA74E1062C1540800000005000000630068006B00310032" \
		         "000C20000001000000000000000100000008000000070000001F7510624C006F006700876563680800000006000000630068" \
		         "006B004C006F0067000C20000001000000000000000100000008000000040000005C4F1A4EE5651F67080000000B00000065" \
		         "0064005000720069006E00740044006100740065000C20000001000000010000000E0000000C200000010000000000000002" \
		         "000000080000000100000004000800000000000000080000000000000008000000000000000C200000010000000000000002" \
		         "00000008000000010000000400080000000000000008000000000000000C2000000100000000000000020000000800000001" \
		         "0000000400080000000000000008000000000000000C20000001000000000000000200000008000000010000000400080000" \
		         "0018000000{planId}{planVer}0800000018000000{planId}{planVer}080000000000000008000000000000000C200000" \
		         "0100000000000000010000000300000001000000080000000200000001959A5B08000000010000004E000800000001000000" \
		         "4E0008000000010000004E0008000000010000004E0008000000010000004E000800000000000000"

		planIdStr = self.__str_to_hex(str(planId))
		planVerStr = self.__str_to_hex(str(planVer))

		__jobId = self.__getJobId()

		self.__mssql.sqlWork(__sqlStrIns.format(hexStr=hexStr.format(planId=planIdStr, planVer=planVerStr),
		                                        jobId=__jobId[0], subId=__jobId[1]))

		self.__log('Insert Job Lock SC Plan: {}'.format(str(planId)))
		return __jobId[0]

	def __lockCgPlan(self, planId, planVer):
		__sqlStrIns = "INSERT INTO DSCSYS.dbo.JOBQUEUE ([JOBID], [SUBID], [COMPANYID], [USERID], [USEDALIAS], [JOBNAME], " \
		              "[EXTNAME], [COMPROGID], [JOBOPTION], [GENTYPE], [GENSTATUS], [PRIORITY], [STATUS], [PROGRESS], " \
		              "[DTREQUEST], [DTRECEIVE], [DTSCHEDULE], [DTSTART], [DTFINISH], [RESULT], [STYLE], [PROCESSER], " \
		              "[FLAG], [NOTIFY]) " \
		              "VALUES ('{jobId}', '{subId}', 'COMFORT', 'Robot', 'COMFORT', 'LRPB04 ', '', " \
		              "'LRPB04S.Class1', {hexStr}, 1, 1, 3, 'N', NULL, getdate(), getdate(), getdate(), " \
		              "NULL, NULL, NULL, 'B', '', 1, '');"

		hexStr = "0x44532056415249414E54202030313030B00300000C2000000100000000000000010000000C20000001000000010000000A" \
		         "0000000C20000001000000000000000100000008000000040000000990E962C154F753080000000400000073007000300031" \
		         "000C20000001000000000000000100000008000000040000000990E962E55D8253080000000400000065006400300032000C" \
		         "20000001000000000000000100000008000000040000000990E962D34E935E080000000400000073007000300033000C2000" \
		         "0001000000000000000100000008000000050000000990E962A44E278DE565080000000400000073007000300034000C2000" \
		         "0001000000000000000100000008000000050000000990E962C7912D8DE565080000000400000073007000300035000C2000" \
		         "0001000000000000000100000008000000060000000990E962A18B12527962F753080000000400000073007000300036000C" \
		         "20000001000000000000000100000008000000060000000990E962A18B1252BA4E5854080000000400000065006400300037" \
		         "000C20000001000000000000000100000008000000060000000990E96201959A5BB672016008000000040000007200670030" \
		         "0038000C20000001000000000000000100000008000000070000001F7510624C006F00670087656368080000000600000063" \
		         "0068006B004C006F0067000C20000001000000000000000100000008000000040000005C4F1A4EE5651F67080000000B0000" \
		         "00650064005000720069006E00740044006100740065000C20000001000000010000000A0000000C20000001000000000000" \
		         "0002000000080000000100000004000800000000000000080000000000000008000000000000000C20000001000000000000" \
		         "000200000008000000010000000400080000000000000008000000000000000C200000010000000000000002000000080000" \
		         "00010000000400080000000000000008000000000000000C2000000100000000000000020000000800000001000000040008" \
		         "0000000000000008000000000000000C200000010000000000000002000000080000000100000004000800000018000000" \
		         "{planId}{planVer}0800000018000000{planId}{planVer}08000000000000000C20000001000000000000000100000003" \
		         "00000001000000080000000200000001959A5B08000000010000004E000800000000000000"

		planIdStr = self.__str_to_hex(str(planId))
		planVerStr = self.__str_to_hex(str(planVer))

		__jobId = self.__getJobId()

		self.__mssql.sqlWork(__sqlStrIns.format(hexStr=hexStr.format(planId=planIdStr, planVer=planVerStr),
		                                        jobId=__jobId[0], subId=__jobId[1]))

		self.__log('Insert Job Lock CG Plan: {}'.format(str(planId)))
		return __jobId[0]

	def __updateFlagTitle(self, planDd):
		__sqlStr = "UPDATE COMFORT.dbo.COPTC SET LRPFLAG = 'Y' WHERE TC001+'-'+RTRIM(TC002) = '{planDd}' "
		self.__mssql.sqlWork(__sqlStr.format(planDd=planDd))
		self.__log('Update Flag - Title: {}'.format(planDd))
