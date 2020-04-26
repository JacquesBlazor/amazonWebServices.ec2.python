# amazonWebServices.ec2.python
AWS (Amazon Web Services) ec2 instances start and stop (running and stopping) by python

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
