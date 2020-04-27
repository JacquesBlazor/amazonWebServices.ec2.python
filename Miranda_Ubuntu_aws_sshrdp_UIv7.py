# --- The MIT License (MIT) Copyright (c) alvinlin, Sat Apr 27 00:59:00pm 2020 ---

# 此程的功能為提供使用 Amazon Web Service (AWS) 的 EC2 服務的使用者一個簡便的使用者界面
# 能夠將每台EC2 Instance(虛擬機器)用Instance ID做成設定檔在使用時可以快速方便地開或/關機
# 方法是在%userprofile%\.aws\目錄建立一個客製的文字檔其副檔名為.aws, 例如 username1.aws
# 同時也用AWS CLI執行AWS Configure以建立%userprofile%\.aws\credentials提供程式存取權限
# --- English Version ---
# The program is intended to provide users who are using EC2 service in AWS (
# Amazon Web Service) to instantly interact with the EC2 instances with a GUI (
# graphical user interface) by instance IDs in a pre-configured text-formatted file.
# To run the program, the AWS credentail should be configured by running AWS CLI. 
# With that, a %userprofile%\.aws\credentials file will be created. Additionaly, 
# you create each of the EC2 instances you have with a profile in %userprofile%\.aws
# folder by setting their credential profile name, instance ID, region and password.

from tkinter import Tk, LabelFrame, Label, Entry, Button, StringVar
import sys, os, logging, json, threading
import boto3

# === 設定程式日誌輸出的等級 ===
logging.basicConfig(level=logging.WARNING, format = '%(levelname)s: %(message)s')
#logging.basicConfig(level=logging.INFO, format = '%(levelname)s: %(message)s')
#logging.basicConfig(level=logging.DEBUG, format = '%(levelname)s: %(message)s')

# === 取得 aws 帳號密碼副程式 ==========
def get_awsconfig():
    configFiles = [ i for i in os.listdir(os.path.expanduser(r'~/.aws/')) if i.lower().endswith('.aws') ]
    if len(configFiles) == 1:
        selectedConfigIndex = 0  # 預設為第 1 個 config profile 
    elif len(configFiles) > 1:
        while True:
            selectedConfig = input(configFiles)
            if not selectedConfig:
                selectedConfigIndex = 0
                break
            elif selectedConfig.isdigit():                
                selectedConfigIndex = int(selectedConfig)
                if selectedConfigIndex < len(configFiles):
                    break
                else:
                    logging.warning(r'你選擇的設定檔號碼 [%s] 超出能選擇的範圖.' % str(selectedConfig))
            else:
                logging.warning(r'你選擇的設定檔號碼 [%s] 超出能選擇的範圖.' % str(selectedConfig))
    else:
        logging.warning(r'無法找到你的 aws 使用者帳號與密碼的設定檔 %userprofile%/.aws/*.aws !')
        # === ** 如果使用 ssh 連線, 設定檔裡的 "Password" 需設定 .pem 的檔案位置, 例如 (* 注意, 使用 ssh 時 Password 為 .pem 的檔案位置)
        logging.warning(r'設定檔格式 ssh 為: {"Profile":"profile username", "Region":"ap-east-2", "ID":"i-01abc234defg5h6j7", "Password":"C://Users//username//.awscredentials//UbuntuServer1804LTSami-5ad2972b.pem"}')
        # === ** 如果使用 rdp 連線, 設定檔裡的 "Password" 需則在 aws console 裡使用 .pem 將密碼解密為明碼後寫在設定檔裡 
        logging.warning(r'設定檔格式 rdp 為:{"Profile":"profile username", "Region":"ap-east-2", "ID":"i-01abc234defg5h6j7", "Password":"@?b!)axcyNKi1SqICn9oSygPx8k(Zm1e"}')        
        return None                
    try:
        configFile = configFiles[selectedConfigIndex]  # 設定為選定的 config profile
    except Exception:
        logging.warning(r'你設定的 aws 使用者帳號與密碼的設定檔: %s 無法使用.' % configFile)
        return None
    try:
        with open(os.path.expanduser(r'~/.aws/%s' % configFile)) as f:
            awsprofile = json.load(f)
    except Exception:
        logging.warning(r'你設定的 aws 使用者帳號與密碼的設定檔: %s 無法使用' % configFile)  
        return None
    if awsprofile['Password'].lower().endswith('.pem'):
        if not os.path.isfile(awsprofile['Password']):
            logging.warning(r'無法找到你在設定檔裡指定的 aws 伺服器 .pem 金鑰檔: %s' % awsprofile['Password'])
            return None
    awsprofile['configFile'] = configFile.rstrip('.aws')  # 把選定的設定檔也做為參數的一部份傳回
    return awsprofile

# === 啟始 aws ec2Instance 物件 ==========
class ec2Instance:
    def __init__(self, accountProfile):
        self.profileName = accountProfile['Profile']
        self.userRegion = accountProfile['Region']
        self.instanceID = accountProfile['ID']
        self.accountPwd = accountProfile['Password']
        self.configFile = accountProfile['configFile']
        try:            
            self.session = boto3.Session(profile_name = self.profileName)
        except Exception:
            logging.warning(r'無法找到你的 aws credentials 設定檔. 可能需要安裝 aws cli 並執行 aws configure. 這樣才會產生 credentials 文件.')
            sys.exit(1)
        else:
            self.client = self.session.client('ec2', region_name = self.userRegion)
    
    # === 開關機狀態及其他參數 ===
    def getStastictics(self):
        self.fqdn = ''  # ' - 尚未開機  - '
        self.ip = '' # ' - 尚未開機  - '
        self.instancedescription = self.client.describe_instances(InstanceIds = [self.instanceID,])
        self.status = self.instancedescription['Reservations'][0]['Instances'][0]['State']['Name']
        if self.status == 'running':
            self.fqdn = self.instancedescription['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicDnsName']
            self.ip = self.instancedescription['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']
    
    # === 開機 ===     
    def setRunning(self):
        if self.status == 'stopped':
            apiResponse = self.client.start_instances(InstanceIds = [self.instanceID,])
            if apiResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
                logging.error('呼叫 API 錯誤: %s' % apiResponse['ResponseMetadata']['HTTPStatusCode'])
                
    # === 關機 ===
    def setStopped(self):
        if self.status == 'running':
            apiResponse = self.client.stop_instances(InstanceIds = [self.instanceID,])
            if apiResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
                logging.error('呼叫 API 錯誤: %s' % apiResponse['ResponseMetadata']['HTTPStatusCode'])

# === 建立 Tk 圖形界面 uiWidgets 物件 =======
class uiWidgets:
    def __init__(self, master):
        self.master = master
        self.master.geometry("%dx%d-%d-%d" % (330, 302, 50, 80))  
        self.master.resizable(False, False)
        self.master.title('%s/%s' % (ec2.configFile, ec2.profileName[ec2.profileName.rfind(' ')+1:]))
        # === 建立圖形界面裡會顯示的變數 =======
        self.startORstop = StringVar()      
        self.showStatus = StringVar()
        self.makeConnection = StringVar()    
        self.showFQDN = StringVar()
        self.showIP = StringVar()
        # === 建立開關機計數器變數 =======
        self.counter = 0
        # === 建立 [設定檔] === User Profile 框架 =======
        self.userprofileFrame = LabelFrame(self.master, text = '設定檔')
        # === 建立 [設定檔] instance ID 標籤與文字 =======
        self.identiferLabel = Label(self.userprofileFrame, text = '載入的 EC2 Inatance ID')
        self.identiferLabel.grid(row = 0, column = 0)
        self.identiferText = Entry(self.userprofileFrame)
        self.identiferText.grid(row = 0, column = 1)
        # === 建立 [設定檔] region 標籤與文字 =======
        self.regionalLabel = Label(self.userprofileFrame, text = '該 EC2 Inatance 的 Region')
        self.regionalLabel.grid(row = 1, column = 0)
        self.regionalText = Entry(self.userprofileFrame)
        self.regionalText.grid(row = 1, column = 1)
        # === 定位 [設定檔] 包裝 User Profile 框架 Frame =======
        self.userprofileFrame.pack(padx = 10, pady = 5, ipadx = 5, ipady = 5)
        # === 插入 [EC2 的 instance ID 文字] 到文字框 =======
        self.identiferText.insert(0, ec2.instanceID)
        # === 插入 [EC2 的 user region 文字] 到文字框 =======
        self.regionalText.insert(0, ec2.userRegion)                  
        # === 建立 [開/關機] start/stop switch 按鈕 =======
        self.switchButton = Button(self.master, textvariable = self.startORstop, width = 10, command = self.switchbuttonClicked)
        # === 定位 [開/關機] start/stop switch 按鈕 =======
        self.switchButton.pack(padx = 10, pady = 5)  
        # === 建立 [目前狀態] instance state 框架 Frame =======
        self.instancestatusFrame = LabelFrame(self.master, text = '目前狀態')
        # === 建立 [目前狀態] instance state 標籤與文字 =======
        self.machinestateLabel = Label(self.instancestatusFrame, text = '目前的 EC2 Inatance 狀態')
        self.machinestateLabel.grid(row = 0, column = 0)
        self.machinestateText = Entry(self.instancestatusFrame, textvariable = self.showStatus)  # 顯示 [EC2 Instance(虛擬機器) 的 State] 
        self.machinestateText.grid(row = 0, column = 1)
        # === 定位 [目前狀態] 包裝 instance state 框架 Frame =======
        self.instancestatusFrame.pack(padx = 10, pady = 5, ipadx = 5, ipady = 5)
        # === 建立 [細節] instance description 框架 Frame =======
        self.statisticsFrame = LabelFrame(self.master, text = '細節')  
        # === 建立 [細節] instance fqdn 標籤與文字 =======
        self.instanceFQDNLable = Label(self.statisticsFrame , text = '目前 EC2 Inatance 的 FQDN')   
        self.instanceFQDNLable.grid(row = 0, column = 0)
        self.instanceFQDNNameText = Entry(self.statisticsFrame , textvariable = self.showFQDN)  # 顯示 [EC2 Instance(虛擬機器) 的 FQDN]          
        self.instanceFQDNNameText.grid(row = 0, column = 1)               
        # ===  建立 [細節] instance ip addr 標籤與文字   =======
        self.instanceIPaddrLable = Label(self.statisticsFrame , text = '目前 EC2 Inatance 的 IP')  
        self.instanceIPaddrLable.grid(row = 1, column = 0)
        self.instanceIPaddrText = Entry(self.statisticsFrame , textvariable = self.showIP)  # 顯示 [EC2 Instance(虛擬機器) 的 IP]                    
        self.instanceIPaddrText.grid(row = 1, column = 1)
        # === 定位 [細節] 包裝 instance description 框架 Frame =======
        self.statisticsFrame.pack(padx = 10, pady = 5, ipadx = 5, ipady = 5)  
        # === 建立 [連線伺服器] make connection 按鈕 =======
        self.connectButton = Button(self.master, textvariable = self.makeConnection, width = 10, command = self.connectbuttonClicked)
        # === 定位 [連線伺服器] make connection 按鈕 =======
        self.connectButton.pack(padx = 10, pady = 5)
        # === 更新所有顯示變數  =======
        self.variablesRefreshing()
    
    # === 更新變數 ===
    def variablesRefreshing(self):
        ec2.getStastictics()
        if ec2.status in ['running', 'stopped']:
            if ec2.status == 'running':
                self.startORstop.set('關機 [Stop]')
                self.makeConnection.set('連線伺服器')
            elif ec2.status == 'stopped':
                self.startORstop.set('開機 [Start]')
                self.makeConnection.set(' - 尚未開機  - ')
        else:
            self.makeConnection.set(' - - - - - ')
        self.showStatus.set(ec2.status)  # EC2 Instance(虛擬機器) 狀態
        self.showFQDN.set(ec2.fqdn)   # EC2 Instance(虛擬機器) 的公開 FQDN 位址
        self.showIP.set(ec2.ip)  # EC2 Instance(虛擬機器) 的公開 IP 位址

    def executeTerminal(self):            
        os.system(self.cmd2exec)

    # === 連線按鈕 ===
    def connectbuttonClicked(self):
        if ec2.status == 'running':
            if ec2.accountPwd.lower().endswith('.pem'):
                self.cmd2exec = 'ssh -o "ServerAliveInterval 40" -o StrictHostKeyChecking=no -i "%s" ubuntu@%s' % (ec2.accountPwd, ec2.fqdn)
            else:
                self.cmd2exec = 'cmdkey /generic:%ec2IP% /user:Administrator /pass:"' + ec2.accountPwd + '" && mstsc /admin /v:%ec2IP%'                 
            try:
                with open(os.path.expanduser(r'~/.aws/%s' % 'executedCmd.aws.txt'), 'w', encoding='utf-8-sig') as f:
                    f.write(self.cmd2exec)  # 將命令列寫入檔案, ** 注意 rdp 包含密碼的明碼
            except Exception:
                logging.warning('執行下列命令寫入桌面檔案錯誤: %s' % self.cmd2exec)
            os.environ['ec2IP'] = ec2.ip            
            cmd = threading.Thread(target=self.executeTerminal)
            cmd.start()
            logging.debug('外部命令視窗啟動是否啟動? %s' % cmd.is_alive())
    
    # === 開關機按鈕 ===
    def switchbuttonClicked(self):
        if ec2.status in ['running', 'stopped']:
            if ec2.status == 'running':  # 如果伺服器EC2 Instance 為啟動中
                ec2.setStopped()  #  ->則關機
            elif ec2.status == 'stopped':
                ec2.setRunning()  # ->否則開機
        self.countingBtn()
    
    # === 按下開關機按鈕後計數 ===
    def countingBtn(self):
        self.counter += 1  # 增加計數
        self.startORstop.set('- - %s - -' % str(self.counter))  # 顯示計數內容
        self.variablesRefreshing()  # 更新畫面上的變數
        if ec2.status not in ['running', 'stopped']:  # 如果狀態已為開或關機表示作業完成                                      
            self.btnSwitchId = self.switchButton.after(2000, self.switchbuttonClicked)  # 否則排定下個2秒(=2000ms)就再更新畫面一次
        else:  
            self.counter = 0
            self.switchButton.after_cancel(self.btnSwitchId)  # 所以取消每2秒更新一次的動作            
        
# === 主程式 ==========
if __name__ == '__main__':
    accountProfile = get_awsconfig()
    if accountProfile:
        ec2 = ec2Instance(accountProfile)
        root = Tk()
        appLayout = uiWidgets(root)
        root.mainloop()
