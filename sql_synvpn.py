#!/usr/bin/python

import shutil
import gzip
import __builtin__
import zlib
import time
import os
import string
#import pickle
import sys
import timeoutsocket


# History log:
# ernad 31.03.04, 17:14 - radio podesenja za planiku-ns, ali nisam testirao
# sasa 11.08.04, 09:30 - promjenio vrijednost var.TRY_LOOPS na 1
# sasa 20.08.04, 11:30 - c:/data1/ ---- d:/data1


WINDOWS = 1
ACTIVE_PYTHON=1

print ("ver 01.16, 02.2002 - 20.08.2004  SC")
print ("-------------------------------------------------------")

if WINDOWS == 1:
	#log direktorij knjigovodstvo
	SQLLogBase='i:\\LOG'
	SQLLogBaseDOS='i:\\LOG'
	Slash="\\"
	EXE_PREFIX ='c:\\sql_synchro\\bin\\'
else:
	SQLLogBase='/var/data1/LOG'
	SQLLogBaseDOS='I:/LOG'
	Slash="/"
	EXE_PREFIX = ''


SQLLogBaseDOSP='C:/SIGMA'

OK_SYNCHRO_COUNT=8
TIMEOUT_TIME=45
#log direktorij prodavnica
SQLLogBaseP=''
fVPN=0
cRemoteHostName='0.0.0.0'
cServerHostName='192.168.77.1'
timeoutsocket.setDefaultSocketTimeout(TIMEOUT_TIME)
TRY_LOOPS=1

LogKnjigovodstvo=0
LogProdavnica=0
# knjigovodstvo site
#k_site='2'
# prodavnica site
#p_site='35'

# sitpe par: 0 = peer
#            1 = site knjigovodstvo
#            2 = site prodavnica
#            3 = host knjigovodstvo
#            4 = host prodavnica
#            5 = privpath knjig
#            6 = kumpath  knjig
#            7 = sifpath  knjig
#            8 = rbr
#            9 = zavrseno
#["prod2" ,"11","51","direktor10.sc","direktor10.sc","I:\\KASE\TOPS\\21","I:\\KASE\\TOPS\\KUM2","I:\\KASE\\SIF2",1,0],\	print ("catujem :" + cmd)
#["prod3" ,"12","52","direktor10.sc","direktor10.sc","I:\\KASE\TOPS\\31","I:\\KASE\\TOPS\\KUM3","I:\\KASE\\SIF3",2,0],\
#]
	


def synchro_k_p (host_p, host_k, k_site, p_site, ftekucistatus ):

	# zakaci se na prodavnicu 
	# uzmi    prodavnica.log
	# posalji knjigovodstvo.log
	# 
	#host prodavnice
	from sc_ftplib import FTP
	

	if (fVPN == 0):
		if (host_k == "VPN"):
			#preskoci prodavnicu
			return 6
	else:
		print "cRemoteHOst", cRemoteHostName
		host_p = cRemoteHostName

	try:
		print "logiram se na "+host_p
		ftp=FTP(host_p)
		ftp.set_pasv(0)
		ftp.login('sc','sc')
	except:
		print("ne mogu se zakaciti na gateway prodavnice")
		return 0
		


	
	print("--------------------------------------------------------")
	print("Proceduru put prodavnica",host_p,k_site,p_site)
	print("--------------------------------------------------------")

	print "osvjezavam verzije ..."
	if ftekucistatus < 1:
		osvjezi_exe(p_site,ftp)

	print("idemo na GSQL komande ...")	
	
	
	if GSQL_HOCU_SYNCHRO(ftp, k_site, p_site) ==0:
		return 1
	
	if GSQL_SET_SVASTA(ftp, k_site, p_site)==0:
		return 1

	if is_ok_synchro(ftp,k_site,p_site)==0:
		return 1
	
	if (ftekucistatus < 2):
		fget = get_prodavnica(ftp,host_k, host_p, k_site,p_site)

		if fget == 0:
			return 1
		elif fget == 4:
			print ("zavrsio get_prodavnica ...")
		else:
			print ("status je negdje izmedju ... ovo jos nije gotovo ...")
			return 1
	
	fsend=0
	if (ftekucistatus < 3):
		fsend = send_k_site(ftp, host_k, host_p, k_site,p_site)
		if fsend==0:
			# nisam uspio sa slanjem k_site log_a
			return 2
	
	
	if (ftekucistatus < 5):
		if (fsend==2) and (ftekucistatus<4):
			# izvrsen je store k_site log-a
			cmd='GSQL GET SQLLOG_DSOFF'+' '+k_site
			resp = ftp.sendcmd(cmd)
			print  'Odgovor na '+cmd+':'+resp
			fUspjesno=0
			if resp=='150 GSQL uspjesna: Import SQL loga zapocet!.':
				fUspjesno=1
				#nema potrebe sada se server otkacio
				#tako da nemam razloga raditi QUIT
				return 6
			else:
				print("Import SQL loga nije uspjesno zapocet ??")
				fUspjesno=0
				return 3
	
		else:
		
			#nije bilo k_site log-a, samo ugasi dial-up server
			#cmd='GSQL SET DIALUP_SRV OFF'
			try:
				#resp = ftp.sendcmd(cmd)
				print  'Odgovor na '   #+cmd+':'+resp
			except:
				print 'komanda nije uspjesno izvrsena: ' # +cmd
				return 4
		

	print "idemo dalje ..."
	
	if (ftekucistatus < 6):
		print "izlazim iz ove ftp sesije"
		resp=""
		try:
			ftp.quit()
		except:
			#print "Posljednji resp:"+ftp.lastresp()
			print "problem pri izlasku"
			return 5
		
		print "izasao "
		return 6

	return 6


def get_prodavnica(ftp, host_k, host_p, site,p_site):
	
	LogProdavnica=1
	#uzimam fajl prodavnice
	resp=""

	try:
		mangle(SQLLogBase+Slash+'SQL'+Slash,p_site,'log')
	except:
		print("problem sa mangle ",SQLLogBase+Slash+'SQL'+Slash+p_site+'.log')
		return 0
			
	print("ucitavam fajl prodavnice (log.gz) ", SQLLogBase+Slash+'SQL'+Slash+p_site+'.log.gz')

	try:
		print(host_p," CWD ",SQLLogBaseDOSP+'/SQL')
		ftp.sendcmd('CWD '+SQLLogBaseDOSP+'/SQL')
	except:
		print("CWD neuspjesna " +SQLLogBaseDOSP+'/SQL')
		return 0
	
	fRetr=0
	try:
		print(host_p," RETR "+p_site+'.log.gz')
		f = __builtin__.open(SQLLogBase+Slash+'SQL'+Slash+p_site+'.log.gz','wb')
		resp = ftp.retrbinary('RETR '+p_site+'.log#gz',f.write,1024)
		print("Odgovor na RETR :", resp)
		if string.find(resp,"NEMA LOG FAJLA!")>-1:
			LogProdavnica=0
			fRetr=0
		else:
			fRetr=1
		f.close()
		
	except:
		print("FTP RETR neuspjesan ? "+p_site+'.log.gz')
		fRetr=0
		resp = ftp.lastresp
		print("Odgovor na RETR:", resp)
		if string.find(resp,"502")>-1:
			LogProdavnica=0
		else:	
			print("nije prekopiran log fajl prodavnice")
			return 0
	
	#za svaki slucaj skloni i ovo da se ne bi desilo da sljedeci prenos uzrokuje gubljenje log-a (prekrivanje log-a starim)
	prebaci_u_sqlbackup(SQLLogBase,'P',p_site,'.gz',0)
	
	

	if fRetr==1:
		try:
			resp = ftp.sendcmd('DELE '+p_site+'.log.gz')
		except:
			print("FTP DELE neuspjesan ?")
			izbrisi_file(SQLLogBase+Slash+'SQL'+Slash+p_site+'.log.gz')
			return 0

		#i=0
		try:
			resp = ftp.sendcmd('DELE '+p_site+'.log')
		except:
			print("FTP DELE log nisam uspio")
			izbrisi_file(SQLLogBase+Slash+'SQL'+Slash+p_site+'.log')
			return 0

	try:
		#promjeni privilegije !!!
		ckom=EXE_PREFIX+"chmod 0770 "+SQLLogBase+Slash+'SQL'+Slash+p_site+'.log.gz'
		os.system(ckom)
		if os.path.isfile(SQLLogBase+Slash+'SQL'+Slash+p_site+'.log'):
			os.remove(SQLLogBase+Slash+'SQL'+Slash+p_site+'.log')
		
		
		# gunzipuj
		ckom=EXE_PREFIX+"gunzip "+SQLLogBase+Slash+'SQL'+Slash+p_site+'.log.gz'
		print("izvrsavam gunzip : "+ckom)
		os.system(ckom)
	
		# Windows doesn't delete original gz file ?
		#if WINDOWS == 1:
		#	ckom="del "+SQLLogBase+Slash+'SQL'+Slash+p_site+'.log.gz'
		#	print(ckom)
		#	os.system(ckom)
			
		print("izvrsavam chmod 0770 "+SQLLogBase+Slash+'SQL'+Slash+p_site+'.log')
		ckom=EXE_PREFIX+"chmod 0770 "+SQLLogBase+Slash+'SQL'+Slash+p_site+'.log'
		os.system(ckom)
	except:
		print("chmod ili gunzip ili chmod neuspjesan ?")
		return 2

	#spoji ako ima vise logova
	
	catuj(SQLLogBase+Slash+'SQL'+Slash, p_site)
	
	try:			
		#Azuriraj Ini parametre prodavnice !!!!
		#resp = ftp.sendcmd("GSQL SET FMKINIPRIV TOPS SamoProdaja D")
		resp = ftp.sendcmd("GSQL SET FMKINIKUM POS Planika D")
		resp = ftp.sendcmd("GSQL SET FMKINIEXE SifRoba DuzSifra 13")
		resp = ftp.sendcmd("GSQL SET FMKINIPRIV POS PorezNaSvakuStavku D")
		resp = ftp.sendcmd("GSQL SET FMKINIKUM TOPS AzuriranjePrometaPoVP D")
		resp = ftp.sendcmd("GSQL SET WININI WINDOWS run ")
	except:
		print("ne mogu setovati INI parametre ?")
		return 3
	
	# uspio RETR, DELE, gunzip, SET *INI
	return 4



def izbrisi_file(cFile):
	cmd=EXE_PREFIX+"rm "+cFile
	os.system(cmd)
	

def send_k_site(ftp, host_k, host_p, k_site,p_site):
	
	#return = 0 - neuspjesno
	#	= 1 - nema sta slati
	#	= 2 - izvrsen je stor k_site loga
	
	LogKnjigovodstvo=1
	
	#bug DOS ne zna napraviti XX.log, zato mi treba donja komanda
	if os.path.isfile(SQLLogBase+Slash+'SQL'+Slash+k_site+'.LOG'):
		cmd=EXE_PREFIX+'mv -f '+SQLLogBase+Slash+'SQL'+Slash+k_site+'.LOG '+SQLLogBase+Slash+'SQL'+Slash+k_site+'.log'
		os.system(cmd)
	
	#postoji 69.log ili 69.log.gz	
	if ( os.path.isfile(SQLLogBase+Slash+'SQL'+Slash+k_site+'.log') or os.path.isfile(SQLLogBase+Slash+'SQL'+Slash+k_site+'.log.gz') ): 
		print("nasao sam log "+SQLLogBase+Slash+'SQL'+Slash+k_site+'.log')
		LogKnjigovodstvo=1
		try:
			if not os.path.isfile(SQLLogBase+Slash+'SQL'+Slash+k_site+'.log.gz'):
				cFile=SQLLogBase+Slash+'SQL'+Slash+k_site+'.log'
				print("kreriram gzip "+cFile+'.gz')
				ckom=EXE_PREFIX+'gzip -f '+cFile
				os.system(ckom)
				if os.path.isfile(cFile+'.gz'):
					print("napravio gzip ..")	
				else:	
					print("ne mogu napraviti gzip ? ")
					return 0
				
		except:
			print("nisam uspio napraviti gzip iz log fajla "+SQLLogBase+Slash+'SQL'+Slash+k_site+'.log')
			LogKnjigovodstvo=0
			return 0
	else:
		print("nema log fajla knjigovodstva nemam sta prebaciti ...")
		LogKnjigovodstvo=1
		return 1


	
	if LogKnjigovodstvo==1:
	
		try:	
			print("saljem log fajl (STOR) "+k_site)
			print("radim CWD "+SQLLogBaseDOSP+'/SQL')
			ftp.sendcmd('CWD '+SQLLogBaseDOSP+'/SQL')
		except:
			print("CWD neuspjesan ?")
			return 0
		
		try:
			print("otvaram log gz:"+k_site+'.log.gz')
			f = __builtin__.open(SQLLogBase+Slash+'SQL'+Slash+k_site+'.log.gz','rb')
		except:
			print("otvaranje log.gz fajla neuspjesno")
			return 0	
	
		try:
			print("izvrsavam stor binary")
			ftp.storbinary('STOR '+k_site+'.log.gz',f,1024)
			print("zatvaram fajl")
			f.close()
		except:
			f.close()
			print("FTP STOR nije uspio ? "+k_site)
			return 0


		#prebaci 10.log u I:/LOG/SQBackupK
		prebaci_u_sqlbackup(SQLLogBase,'K',k_site,'.gz',1)
	
	return 2
	
	
def napravi_krug(siteparovi):

	imajos=0
	for peer, k_site, p_site, host_k, host_p, privpath_k, kumpath_k,sifpath_k,rbr,zavrseno, sleep in  siteparovi:
		print("Par:", peer , k_site, p_site, sleep, zavrseno)
		lNoConnection = 0
		if (fVPN == 0) :
			time.sleep(2)
		if ( zavrseno < 6 ) :
			nRez=0
			try:

				if (fVPN==0):
					if WINDOWS==1:
						pppdstop(peer)
					else:
						#pokusaj se otkaciti dva puta
						if aktivan_192_169(peer):
							print "veza je aktivna ???"
							time.sleep(3)
							pppdstop(peer)
					
						if aktivan_192_169(peer):
							print "veza opet aktivna ????"
							time.sleep(10)
							pppdstop(peer)

					if (host_k == "VPN"):
						return 1

					pppdcall(sleep, peer)

				
				if (fVPN==0):
					if aktivan_192_169(peer)==0:
						print "nisam se zakacio "+host_p
						zavrseno=0
						imajos=imajos+1
						#continue
						lNoConnection = 1
				
				#nRez = os.system(ckom)
			
			except:
				print("ne mogu se spojiti greska=",nRez)
				zavrseno=0
				imajos=imajos+1
				#continue
				lNoConnection = 1
				
			
			if lNoConnection == 0:
				zavrseno = synchro_k_p (host_p,host_k, k_site,p_site, zavrseno)
				siteparovi[rbr][9] = zavrseno

			if zavrseno == 6:
				print("syhchro ok")

			else:
				print("moracemo ponovo")
				zavrseno=0
				imajos=imajos+1
	
	
			if (fVPN == 0):
				pppdstop(peer)
	
	return imajos


def odstampaj_siteparovi():
	
	for peer,k_site,p_site,h_k,h_p,pp_k,kp_k,sp_k,rbr,zavrseno,sleep in siteparovi:
		print(rbr,peer,k_site,p_site,zavrseno,sleep)
			


def vrti_dok_ne_zavrsis(siteparovi, samoprodavnice):
	
	count=0
	while 1:
		print ("")
		count=count+1
		print ("Pozivanje prodavnica krug :",count)
		for f in range(0,1):
			print ("=====================================================")
		imajos=napravi_krug(siteparovi)
		if imajos==0:
			break
			#nemavise !!!!
		if count==TRY_LOOPS:
			print ""
			print ""
			print "--------------++++++++++PROSAO " + str(TRY_LOOPS) + " KRUGOVA +++++++++++------------------"
			print ""
			print ""
			break
	
	odstampaj_siteparovi()
	return



def prebaci_u_sqlbackup(cSQLLOGBASE,cOznaka,logname, gzip , fUkloniti):

	print("izvrsavam prebaci_u_sqlbackup")
	cSQLLog=cSQLLOGBASE+Slash+'SQL'+Slash+logname+'.log'+gzip
	i=0
	while 1:
		i=i+1
		cBackupF= cSQLLOGBASE + Slash+'SQLBackup'+cOznaka+Slash+logname+'_'+dtos()+'_'+str(i)+'.log'+gzip
		if not os.path.isfile(cBackupF):
			break

	print("kopiram iz - u ",cSQLLog,cBackupF)
	shutil.copyfile(cSQLLog, cBackupF)

	if fUkloniti==1:
		cmd=EXE_PREFIX+"rm "+cSQLLog
		print("izvrsavam "+cmd)
		os.system(cmd)
	
	
def mangle(cSQLLogBase,cFile,cEXT):
	
	# /var/data1/LOG/SQL/50.log
	if os.path.isfile(cSQLLogBase+cFile+'.'+cEXT):
		cImali=cSQLLogBase+cFile+'.'+cEXT
		i=0
		while 1:
			i=i+1
			cMangle = cSQLLogBase+cFile+'_'+str(i)+'.' + cEXT
			if not os.path.isfile(cMangle):
				break
		print("kopiram iz - u ",cSQLLogBase+cFile+'.'+cEXT,cMangle)
		shutil.copyfile(cSQLLogBase+cFile+'.'+cEXT, cMangle)
	else:
		return 0

	return 1


	
def snimi_stanje(siteparovi):
	
	if (fVPN == 0):
		#f = __builtin__.open("/var/data1/LOG/"+dtos()+".stanje","wb")
		#p = pickle.Pickler(f)
		#p.dump(siteparovi)
		#f.close()
		return 0
	return 0

def ucitaj_stanje():

	#f = __builtin__.open("/var/data1/LOG/"+dtos()+".stanje","rb")
	#tmp = pickle.load(f)
	#f.close()
	#return tmp
	return 0

	
def dtos():
	ltime=  time.localtime(int (time.time()))
	return time.strftime("%Y%m%d", ltime)

def USamoProdavnice(samoprodavnice,prod):
	for p in samoprodavnice:
		#print "uporedjujem",p,prod
		if p==prod:
			#print "nasao jednako"
			return 1
	return 0


def pppdcall(sleep, peer):

	#0 - uspjesna operacija, <>0 neuspjesna operacija

	if WINDOWS == 1:
		# samo ako veza nije aktivna, zovi prodavnicu
		if  aktivan_192_169 (peer) == 0:
			ckom="rasdial prodavnica_"+peer+" prodavnica_"+peer+" 10"
			print ckom
			nRez=os.system(ckom)
			if nRez==0:
				return 0
			else:
				return 1
		else:
			# veza je vec bila aktivna
			return 0
	else:
		ckom="/usr/sbin/pppd_w95 call "+ peer+" &"
		print "malo cemo pricekati uspostavljanje veze ..."
		nRez=os.system(ckom)
		time.sleep(sleep)
		return 0
	
	
def pppdstop(peer):

	#0 - uspjesna operacija, <>0 neuspjesna operacija
	
	if WINDOWS == 1:
		ckom = "rasdial prodavnica_"+peer+" /DISCONNECT" 
		nRez = os.system(ckom)
		if nRez == 0:
			return 0
		else:
			return 1
		
	else:
	
		if (fVPN == 1):
			return 0
	
    		try:	
			ckom="/usr/sigma/scripts/kill_pppd_w95"
			os.system(ckom)
			#time.sleep(8)
		except:
			print "nisam uspio pppd stop"
		return 0
	

def aktivan_192_169 (peer):
	if WINDOWS==1:
		time.sleep(5)
		cmd = "rasdial | "  + EXE_PREFIX + "grep_borland Prodavnica_"+peer
		#cmd = "rasdial | "  + "grep " + "'"+"prodavnica_"+peer+"'"
		print(cmd)
		nRez = os.system(cmd)
		print "os.system=", nRez
		if nRez == 0:
			#veza aktivna
			return 1
		else:
			return 0	
		
	else:
		cmd = "/usr/sigma/scripts/aktivan_192_169.py"
		nRez = os.system(cmd)
		if (nRez == 0):
			#aktivan
			return 1
		else:
			return 0
		
def GSQL_HOCU_SYNCHRO(ftp,k_site,p_site):
	
	resp=''
	cmd='GSQL IMSG HOCU_SYNCHRO '+k_site
	try:	
		resp = ftp.sendcmd(cmd)
		print "Odgovor na "+cmd+':'+resp
	except:
		print "nije uspjela komanda hocu synchro ??"
		return 0
	
	return 1
		

def GSQL_SET_SVASTA(ftp,k_site,p_site):
	
	try:
		cmd='GSQL SET TABLE_DIRSIF #ROBA#SIFK#SIFV#OSOB#TARIFA#VALUTE#VRSTEP#ODJ#UREDJ#STRAD#'
		while 1:	
			resp = ftp.sendcmd(cmd)
			print "Odgovor na "+cmd+':'+resp
			#f resp[:1]=='1':
			break
		cmd='GSQL SET TABLE_DIRKUM #POS#DOKS#KPARAMS#PROMVP#'
		while 1:	
			resp = ftp.sendcmd(cmd)
			print "Odgovor na "+cmd+':'+resp
			#f resp[:1]=='1':
			break

		cmd='GSQL SET TABLE_DIRPRIV #PARAMS#'
		while 1:	
			resp = ftp.sendcmd(cmd)
			print "Odgovor na "+cmd+':'+resp
			#f resp[:1]=='1':
			break

		cmd='GSQL SET DIRKUM C:\\TOPS\\KUM1'
		while 1:	
			resp = ftp.sendcmd(cmd)
			print "Odgovor na "+cmd+':'+resp
			#f resp[:1]=='1':
			break
		cmd='GSQL SET DIRSIF C:\\TOPS\\SIF'
		while 1:	
			resp = ftp.sendcmd(cmd)
			print "Odgovor na "+cmd+':'+resp
			#f resp[:1]=='1':
			break

		cmd='GSQL SET DIRPRIV C:\\TOPS\\11'
		while 1:	
			resp = ftp.sendcmd(cmd)
			print "Odgovor na "+cmd+':'+resp
			#f resp[:1]=='1':
			break

	except:
		#nisam mogao setovati parametre
		return 0
	
	return 1



def is_ok_synchro(ftp,k_site,p_site):
	
	fOk=0
	sacekaj=0
	
	try:
		time.sleep(10)
		while 1:
			cmd='GSQL IMSG OK_SYNCHRO_?'
			#+' '+k_site
			question=1
			while 1:	
				resp = ftp.sendcmd(cmd)
				print 'Odgovor na '+cmd+":"+resp
				#2 je ok
				question=question+1
				
				if resp=='150 GSQL uspjesna: OK_SYNCHRO.':
					fOk=1
					break
				
				elif resp=='150 GSQL uspjesna: SACEKAJ.':
					fOk=0
					print "udaljena strana trazila da sacekam"
					GSQL_HOCU_SYNCHRO(ftp, k_site)
					sacekaj=sacekaj+1
					break
			
				if question==OK_SYNCHRO_COUNT:
					#tops nije ukljucen ipak nastavi posao
					fOk=1
					break
				time.sleep(10)
			if fOk==1:
				break
			else:
				if sacekaj>3:
					if (fVPN == 0):
						pppdstop()
					return 0
	except:
		return 0
	
	return fOk


def imaliuredjaja (cur):

	ckom="/sbin/ifconfig | grep ^"+cur	
	nRez=os.system(ckom)
	print "Uredjaj "+cur+":" + str(nRez)
	
	if nRez==0:
		#uredjaj postoji
		return 1
	else:
		return 0

def osvjezi_exe(p_site,ftp):
	
	# sc_osvjezi se mora direktno u EXE direktorij staviti
	try:	
		print("radim CWD C:/TOPS")
		ftp.sendcmd('CWD C:/TOPS')
	except:
		print("CWD neuspjesan ?")

	prenesi_izosvjezi("test.txt",p_site, ftp)
	prenesi_izosvjezi("sc_osvjezi.exe",p_site, ftp)
	try:	
		print("radim CWD "+SQLLogBaseDOSP+'/OSVJEZI')
		ftp.sendcmd('CWD '+SQLLogBaseDOSP+'/OSVJEZI')
	except:
		print("CWD neuspjesan ?")
		try:
			print("kreiram direktorij MD")
			ftp.sendmcmd('MD '+SQLLogBaseDOSP+'/OSVJEZI')
			print("ponovo pokusavam CWD")
			ftp.sendcmd('CWD '+SQLLogBaseDOSP+'/OSVJEZI')
		except:
			print("ne mogu kreirati direktorij")
			return 0
	prenesi_izosvjezi("lokacije.ini",p_site, ftp)
	prenesi_izosvjezi("TOPS.EXE.gz",p_site, ftp)
	prenesi_izosvjezi("GATEWAY.EXE.gz",p_site, ftp)
	prenesi_izosvjezi("gateway.exe.gz",p_site, ftp)
	prenesi_izosvjezi("ITOPS.EXE.gz", p_site, ftp)
	return 1



def catuj( cDirektorij, cSite ):
	
	#cSite=str(nSite)
	#print "Site je ", cSite
	if not os.path.isfile(cDirektorij + cSite+"_1.log"):
		#print "nemam sta raditi"
		return

	#if WINDOWS == 1:
	#	#radim cut-ovanje
	#	cmd="cat "+cDirektorij + cSite+"*.log > "+cDirektorij+"cat_"+cSite+".log"
	#	os.system(cmd)
	#	cmd="del "+cDirektorij+cSite+"*.log"
	#	os.system(cmd)
	#	cmd="copy "+cDirektorij+"cat_"+cSite+".log "+cDirektorij+cSite+".log"
	#	os.system(cmd)
	#	cmd="del "+cDirektorij+"cat_"+cSite+".log"
	#	os.system(cmd)
	#else:
	#radim cut-ovanje
	if WINDOWS == 1:
		#cmd = "c:\\sql_synchro\\cat_logs_dos.bat " + cDirektorij + " " + cSite
		cmd = "copy "+cDirektorij+cSite+"_1.log" + "+" + cDirektorij+cSite+".log" + " " + cDirektorij + "cat_"+cSite+".log"
		print ("catujem-1 :" + cmd)
		os.system(cmd)
		cmd = EXE_PREFIX+"rm "+cDirektorij+cSite+"_1.log"
		print ("catujem-2 :" + cmd)
		os.system(cmd)
		cmd = EXE_PREFIX+"rm "+cDirektorij+cSite+".log"
		print ("catujem-3 :" + cmd)
		os.system(cmd)
		cmd = EXE_PREFIX+"mv "+cDirektorij+"cat_"+cSite+".log" + " " + cDirektorij+cSite+".log" 
		print ("catujem-4 :" + cmd)
		os.system(cmd)

	else:
		cmd=EXE_PREFIX+"cat "+cDirektorij + cSite+"*.log > "+cDirektorij+"cat_"+cSite+".log"
		os.system(cmd)
		cmd=EXE_PREFIX+"rm "+cDirektorij+cSite+"*.log"
		os.system(cmd)
		cmd=EXE_PREFIX+"mv "+cDirektorij+"cat_"+cSite+".log "+cDirektorij+cSite+".log"
		os.system(cmd)

	#promjeni privilegije !!!
	cmd="chmod 0770 "+cDirektorij+cSite+'.log'
	os.system(cmd)


def prenesi_izosvjezi(cFile, p_site, ftp ):

	cPom=SQLLogBase+Slash+'OSVJEZI'+Slash+p_site+Slash+cFile
	if not os.path.isfile(cPom):
		print("fajla "+cPom+" nema ... nemam sta osvjezavati")
		return 1
	

	try:
			
		print("otvaram "+cPom)
		f = __builtin__.open(cPom,'rb')
	except:
		print("otvaranje fajla neuspjesno")
		return 0
	
	try:
		print("izvrsavam stor binary "+cFile)
		ftp.storbinary('STOR '+cFile+'.tmp' , f , 1024)
		f.close()
	except:
		f.close()
		print("nije uspio stor")
		return 0

	try:
        	ftp.sendcmd('DELE '+cFile)
	except:
		print("nemam sta brisati")
	
	try:
        	ftp.sendcmd('RNFR '+cFile+'.tmp')
		ftp.sendcmd('RNTO '+cFile)
		print("zatvaram fajl")
	except:
		print("rename nije uspio")
		return 0
	
	try:
		cmd=EXE_PREFIX+"mv -f "+cPom+" "+SQLLogBase+Slash+'OSVJEZI'+Slash+p_site+Slash+'old'+Slash+cFile
		print("izvrsavam:", cmd)
		os.system(cmd)
	except:
		print("nisam uspio napraviti move")
		
	return 1


if __name__== '__main__':
	
    	siteparovi=[]
	
	if WINDOWS == 0:
		print imaliuredjaja("eth0")
	  	
	#prodavnica 1 - grbavica soping centar
 	ite=["50"  ,"10","50","VPN","10.7.1.11","I:\\KASE\TOPS\\11","I:\\KASE\\TOPS\\KUM1","I:\\KASE\\SIF1",0,0,70]
	siteparovi.append(ite)
	
	#prodavnica 2 - alipasino polje
	ite=["51"  ,"11","51","VPN","10.7.1.12","I:\\KASE\TOPS\\21","I:\\KASE\\TOPS\\KUM2","I:\\KASE\\SIF2",1,0,70]
	siteparovi.append(ite)
	
	#prodavnica 3 - ovo je gril i on se ne koristi !!!!!
	ite=["52"  ,"12","52","VPN","10.7.1.999","I:\\KASE\TOPS\\31","I:\\KASE\\TOPS\\KUM3","I:\\KASE\\SIF3",2,0,70]
	siteparovi.append(ite)

	#prodavnica 4 - breza
	ite=["53"  ,"13","53","VPN","10.7.1.13","I:\\KASE\TOPS\\41","I:\\KASE\\TOPS\\KUM4","I:\\KASE\\SIF4",3,0,70]
	siteparovi.append(ite)

	#prodavnica 5 - i ovo je gril, ne koristi se!!!
	ite=["54"  ,"14","54","VPN","10.7.1.999","I:\\KASE\TOPS\\51","I:\\KASE\\TOPS\\KUM5","I:\\KASE\\SIF5",4,0,70]
	siteparovi.append(ite)

    #prodavnica 6 - env.sehovica VPN
	ite=["55"  ,"15","55","VPN","10.7.1.14","I:\\KASE\TOPS\\61","I:\\KASE\\TOPS\\KUM6","I:\\KASE\\SIF6",5,0,70]
	siteparovi.append(ite)

    #prodavnica 7 - bolnicka
	ite=["56"  ,"16","56","VPN","10.7.1.15","I:\\KASE\TOPS\\71","I:\\KASE\\TOPS\\KUM7","I:\\KASE\\SIF7",6,0,70]
	siteparovi.append(ite)		

	#prodavnica 8 - hamdije cemerlica - safet VPN
	ite=["57"  ,"17","57","VPN","10.7.1.16","I:\\KASE\TOPS\\81","I:\\KASE\\TOPS\\KUM8","I:\\KASE\\SIF8",7,0,70]
	siteparovi.append(ite)	

	#prodavnica 9 - grbavicka
	ite=["58"  ,"18","58","VPN","10.7.1.17","I:\\KASE\TOPS\\91","I:\\KASE\\TOPS\\KUM9","I:\\KASE\\SIF9",8,0,70]
	siteparovi.append(ite)

	#prodavnica 10 - gril koji se ne koristi !!!!
	ite=["59"  ,"19","59","VPN","10.7.1.999","I:\\KASE\TOPS\\101","I:\\KASE\\TOPS\\KUM10","I:\\KASE\\SIF10",9,0,70]
	siteparovi.append(ite)

	#prodavnica 11 - hrasno - porodice ribar VPN
	ite=["60"  ,"20","60","VPN","10.7.1.19","I:\\KASE\TOPS\\111","I:\\KASE\\TOPS\\KUM11","I:\\KASE\\SIF11",10,0,70]
	siteparovi.append(ite)

	#prodavnica 12 - dzemala bijedica
	ite=["61"  ,"21","61","VPN","10.7.1.20","I:\\KASE\TOPS\\121","I:\\KASE\\TOPS\\KUM12","I:\\KASE\\SIF12",11,0,70]
	siteparovi.append(ite)

	#prodavnica 13 - isovica sokak
	ite=["62"  ,"22","62","VPN","10.7.1.21","I:\\KASE\TOPS\\131","I:\\KASE\\TOPS\\KUM13","I:\\KASE\\SIF13",12,0,70]
	siteparovi.append(ite)

	#prodavnica 14 - konjic
	ite=["63"  ,"23","63","VPN","10.7.1.18","I:\\KASE\TOPS\\141","I:\\KASE\\TOPS\\KUM14","I:\\KASE\\SIF14",13,0,70]
	siteparovi.append(ite)
	
	#prodavnica 15 - zmaja od bosne
	ite=["64"  ,"24","64","VPN","10.7.1.22","I:\\KASE\TOPS\\151","I:\\KASE\\TOPS\\KUM15","I:\\KASE\\SIF15",14,0,70]
	siteparovi.append(ite)
	
	#prodavnica 16 - muhameda hadzijahica
	ite=["65"  ,"25","65","VPN","10.7.1.23","I:\\KASE\TOPS\\161","I:\\KASE\\TOPS\\KUM16","I:\\KASE\\SIF16",15,0,70]
	siteparovi.append(ite)

	#prodavnica 17 - azize sacirbegovic
	ite=["66"  ,"26","66","VPN","10.7.1.24","I:\\KASE\TOPS\\181","I:\\KASE\\TOPS\\KUM18","I:\\KASE\\SIF18",16,0,70]
	siteparovi.append(ite)
	
	#prodavnica 18 - fetaha becirbegovica
	ite=["67"  ,"27","67","VPN","10.7.1.25","I:\\KASE\TOPS\\171","I:\\KASE\\TOPS\\KUM17","I:\\KASE\\SIF17",17,0,70]
	siteparovi.append(ite)

	#mostar 19 - mostar
	ite=["68"  ,"28","68","VPN","10.7.1.26","I:\\KASE\TOPS\\191","I:\\KASE\\TOPS\\KUM19","I:\\KASE\\SIF19",18,0,70]
	siteparovi.append(ite)

	#prijedor 20 - prijedor
	ite=["69"  ,"29","69","VPN","10.7.1.27","I:\\KASE\TOPS\\201","I:\\KASE\\TOPS\\KUM20","I:\\KASE\\SIF20",19,0,50]
	siteparovi.append(ite)

    #prodavnica 21 - mostar 2 VPN
	ite=["70"  ,"30","70","VPN","10.7.1.29","I:\\KASE\TOPS\\211","I:\\KASE\\TOPS\\KUM21","I:\\KASE\\SIF21",20,0,70]
	siteparovi.append(ite)

	fVPN=0
	fNeUcitavaj=0
	fShutdown=0
	samoprodavnice=[]
	fZadaneProdavnice=0
	fUzmiHostName=0
	for prodavnica in sys.argv[1:]:
		param = prodavnica
		#print "param je ",param[0],param[1]
		if param[0]=='/':
			cFlag=param[1:4]
			if cFlag=='VPN':
				fVPN=1
				fUzmiHostName = 1
				TRY_LOOPS=1


			if cFlag=='X':
				fShutdown=1
			if cFlag=='0':
				print "parametar /0 => necu ucitavati siteparovi iz fajla"
				fNeUcitavaj=1
		else:
			if fUzmiHostName:
				#print "prodavnica : ", prodavnica
				cRemoteHostName = prodavnica
				fUzmiHostName = 0
			else:
				samoprodavnice.append(prodavnica)
				fZadaneProdavnice=1
		
	#ucitaj siteparovi iz *.stanje fajla
	if WINDOWS == 0:
		if fNeUcitavaj==0:	
			if (fVPN == 0):
				if os.path.isfile(cSQLLogBase+Slash+dtos()+'.stanje'):
					siteparovi = ucitaj_stanje()
				else:
					snimi_stanje(siteparovi)


	
	if samoprodavnice.count>0:
		print "Navedene su prodavnice koje zelite obraditi:", samoprodavnice
		for site in siteparovi:
			#print "site[2], site[8] site[9] ", site[2], site[8], site[9]
			if USamoProdavnice(samoprodavnice, site[2])==1:
				#definisi da ovaj site treba raditi, te je polje zavrseno = 0
				if fShutdown==0:
					siteparovi[site[8]][9]=0
				else:
					siteparovi[site[8]][9]=4
			else:
				#ovu prodvanicu ne treba raditi 
				if fZadaneProdavnice==1:
					siteparovi[site[8]][9]=6
				else:
					siteparovi[site[8]][9]=0
					
		if (fVPN==0):
			print "--------------------------------------------------"
			print "ostampacu site parove:"
			odstampaj_siteparovi()
			print "--------------------------------------------------"
		
	vrti_dok_ne_zavrsis(siteparovi, samoprodavnice)
	
	snimi_stanje(siteparovi)
	print ""
	print ""
	odstampaj_siteparovi()

	if (fVPN == 1):
		for site in siteparovi:
			if (site[9] != 6):
				print "*** VPN exit code = -1"
				sys.exit(-1)
		

	if (fVPN == 1):
		print "*** VPN exit code = 0"
		sys.exit(0)
