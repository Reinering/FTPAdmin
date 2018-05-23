# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
"""
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow

from Ui_FTPAdmin import Ui_MainWindow
from PyQt5.QtGui import QPixmap
import telnetlib
import time
import subprocess
from ftplib import FTP

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self._translate = QtCore.QCoreApplication.translate
        self.tl = TelnetDev()
        self.userList = []
    # 提权
    def sudo(self, msg, title, information):
        if "-bash:" in msg:
            error = QtWidgets.QMessageBox.critical(self, title, information)
            return False
        elif "[sudo] ftpadmin" in msg:
            self.tl.exec_cmd(self.lineEdit_passwd.text() + "\r\n")
            msg = self.tl.read_very_eager()
            if "[sudo] ftpadmin" in msg:
                QtWidgets.QMessageBox.critical(self, u"登陆检查", u"请检查用户名密码，确认无误后请重新操作")
                return False
            if "-bash-4.2$" in msg:
                return True
        elif "-bash-4.2$" in msg:
            return True

    # 获得现有用户
    def getUser(self):
        self.tl.exec_cmd("cat /etc/vsftpd/vuser_list" + "\r\n")
        msg = self.tl.read_very_eager()
        tmpList = msg.split('\r\n')
        print("用户列表：", tmpList)
        userConfList = []
        if tmpList[0] == "cat /etc/vsftpd/vuser_list":
            tmpList = tmpList[1:]
        if "-bash-4.2$" in tmpList[-1]:
            userConfList = tmpList[:-1]

        print(userConfList)
        n = 0
        self.userList = []
        while n < len(userConfList):
            self.userList.append(userConfList[n])
            n += 2
        print(self.userList)
        return self.userList

    # 设置用户ComboBox
    def setComboBox_userList(self, userList):
        self.comboBox_userList.clear()
        i = 0
        if userList:
            for tmp in userList:
                print("tmp", tmp)
                if tmp == "ftptester":
                    continue
                self.comboBox_userList.addItem("")
                self.comboBox_userList.setItemText(i, self._translate("MainWindow", tmp))
                i += 1

    # 新增
    @pyqtSlot()
    def on_pushButton_add_clicked(self):
        """
        Slot documentation goes here.
        """
        model = self.lineEdit_model.text()
        customer = self.lineEdit_customer.text()
        if model == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"设备型号不能为空")
            return
        if customer == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"运营商不能为空")
            return

        if not self.login():
            return
        time.sleep(1)

        dirname = model + "_" + customer
        if not self.userList:
            userList = self.getUser()
            self.setComboBox_userList(userList)
        if dirname in self.userList:
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"此用户已存在，若忘记密码请更新密码。")
            return

        self.tl.exec_cmd("sudo sh -c \'echo \"" + dirname +"\" >> /etc/vsftpd/vuser_list\'" + "\r\n")
        msg = self.tl.read_very_eager()

        if not self.sudo(msg, u"新增", u"新增账户错误"):
            return
        self.lineEdit_user.setText(dirname)

        self.tl.exec_cmd("sudo sh -c \'echo \"" + "00000000" + "\" >> /etc/vsftpd/vuser_list\'" + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"新增", u"新增账户密码错误"):
            return
        self.lineEdit_pwd.setText("00000000")

        self.tl.exec_cmd("sudo db_load -T -t hash -f /etc/vsftpd/vuser_list  /etc/vsftpd/vuser_list.db" + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"新增", u"数据库更新错误"):
            return

        self.tl.exec_cmd("sudo touch /etc/vsftpd/vuserconf/" + dirname + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"新增", u"创建配置文件失败"):
            return

        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "local_root=/home/data/ftp/product/" + dirname + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "anonymous_enable=NO" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "write_enable=NO" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "local_umask=022" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "anon_upload_enable=NO" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "anon_mkdir_write_enable=NO" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "idle_session_timeout=600" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "data_connection_timeout=120" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "max_clients=10" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        self.tl.exec_cmd(
            "sudo sh -c \'echo \"" + "max_per_ip=5" + "\" >> /etc/vsftpd/vuserconf/" + dirname + "\'" + "\r\n")
        msg = self.tl.read_very_eager()
        if "bash：" in msg:
            error = QtWidgets.QMessageBox.critical(self, u"新增", u"创建配置文件失败")
            return

        # self.tl.exec_cmd("sudo chown -R root.root /etc/vsftpd/vuserconf/" + dirname + "\r\n")
        # msg = self.tl.read_very_eager()
        # if not sudo(msg, u"新增", u"创建目录失败"):
        #     return

        self.tl.exec_cmd("sudo mkdir /home/data/ftp/product/" + dirname + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"新增", u"创建目录失败"):
            return

        self.tl.exec_cmd("sudo chown -R ftpadmin.root /home/data/ftp/product/" + dirname + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"新增", u"目录权限更改失败"):
            return
        self.tl.exec_cmd("sudo chmod 750  /home/data/ftp/product/" + dirname + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"新增", u"目录权限更改失败"):
            return

        self.tl.close("exit" + "\r\n")
        information = QtWidgets.QMessageBox.information(self, u"提示", u"操作完成")


    # 刷新
    @pyqtSlot()
    def on_pushButton_refresh_clicked(self):
        """
        Slot documentation goes here.
        """
        if not self.login():
            return
        time.sleep(0.5)

        userList = self.getUser()
        self.setComboBox_userList(userList)
        self.tl.close("exit" + "\r\n")
        information = QtWidgets.QMessageBox.information(self, u"提示", u"刷新完成")

    # 密码更新
    @pyqtSlot()
    def on_pushButton_update_clicked(self):
        """
        Slot documentation goes here.
        """
        user = self.comboBox_userList.currentText()
        newPWD = self.lineEdit_newPasswd.text()

        print(user)
        if user == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"需要更新的用户名为空，请确认后操作")
            return
        if newPWD == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"需要更新的密码为空，请确认后操作")
            return

        index = self.userList.index(user)
        print(index)
        if (index%2) == 0:
            warning = QtWidgets.QMessageBox.critical(self, u"提示", u"用户列表获取错误或ftp用户文件错误，请核对后重试")
            return

        if not self.login():
            return
        time.sleep(0.5)

        # 增加新密码
        self.tl.exec_cmd("sudo sed -i \'" + str(index*2 + 2) + "i " + newPWD + "\' /etc/vsftpd/vuser_list" + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"更新密码", u"更新密码错误"):
            return

        # 删除原密码
        self.tl.exec_cmd("sudo sed -i \'" + str(index*2 + 2 + 1) + "d\' /etc/vsftpd/vuser_list" + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"更新密码", u"删除原密码错误"):
            return

        # 重新生成数据库
        self.tl.exec_cmd("sudo db_load -T -t hash -f /etc/vsftpd/vuser_list  /etc/vsftpd/vuser_list.db" + "\r\n")
        msg = self.tl.read_very_eager()
        if not self.sudo(msg, u"新增", u"数据库更新错误"):
            return

        self.tl.close("exit" + "\r\n")
        information = QtWidgets.QMessageBox.information(self, u"提示", u"更新完成")

    # 获取链路状态
    def getLinkState(self, ip):
        ping_True = False
        # 运行ping程序
        num = 0
        while num < 5:
            time.sleep(1)
            p = subprocess.Popen("ping %s -w 100 -n 1" % (ip),
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)

            # 得到ping的结果
            # print(p.stdout.read())
            out = str(p.stdout.read(), encoding="gb2312", errors="ignore")
            print('ont:', out)

            # #找出丢包率，这里通过‘%’匹配
            # regex = re.compile(r'\w*%\w*')
            # packetLossRateList = regex.findall()
            if 'Request timed out' in out:
                print('Request timed out')
            elif 'General failure' in out:
                print('General failure')
            elif "Destination host unreachable" in out:
                print("Destination host unreachable")
            elif "Destination net unreachable" in out:
                print("Destination net unreachable")
            elif "丢失 = 1 " in out:
                print("丢失 = 1 ")
            elif "字节=32" in out:
                print("字节=32")
                ping_True = True
                break
            elif 'bytes=32' in out:
                print('bytes=32')
                ping_True = True
                break
            num += 1
        print(ping_True)
        return ping_True

    # 登陆
    def login(self):
        ip = self.lineEdit_ipAddr.text()
        username = self.lineEdit_username.text()
        passwd = self.lineEdit_passwd.text()
        if ip == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"IP地址不能为空")
            return
        if username == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"用户名不能为空")
            return
        if passwd == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"登陆密码不能为空")
            return

        login_Method = "Telnet"
        telnet_prompt = []
        if ip == "192.168.186.186":
            telnet_prompt = ["MiWiFi-R1CM-srv login:", "Password:"]
        elif ip == "10.110.30.86":
            telnet_prompt = ["localhost login:", "Password:"]
        if not self.getLinkState(self.lineEdit_ipAddr.text()):
            # warning = QtWidgets.QMessageBox.warning(self, u"网络连接检查", u"请检查配置网络是否连接正常，确认无误后请重新操作")
            # information = QtWidgets.QMessageBox.information(self, u"提示", u"操作完成")
            # question = QtWidgets.QMessageBox.question(self, u"询问", u"Of Course, I still love you")
            #about = QtWidgets.QMessageBox.about(self, u"关于", u"关于你是否还爱着我")
            error = QtWidgets.QMessageBox.critical(self, u"网络连接检查", u"请检查配置网络是否连接正常，确认无误后请重新操作")
            return False

        if login_Method == "Telnet":
            try:
                self.tl.auth(ip, 23, username + "\r\n", passwd + "\r\n",
                                     telnet_prompt)
                time.sleep(1)
                msg = self.tl.read_very_eager()
                if "-bash-4.2$" not in msg:
                    QtWidgets.QMessageBox.critical(self, u"登陆检查", u"请检查用户名密码，确认无误后请重新操作")
                    return False
                return True
            except Exception as e:
                print("Telnet登陆错误：", e)
                QtWidgets.QMessageBox.critical(self, u"登陆检查", u"请检查用户名密码，确认无误后请重新操作")
                return False

        elif login_Method == "SSH2":
            try:
                self.ssh_OLT.auth(self.olt_Ipaddr, 22, self.olt_User, self.olt_Passwd)
                self.olt_LinkState = True
                self.logQueue.put(self.olt_Fact + " OLT IP地址：" + self.olt_Ipaddr + " SSH2 已登陆")
                return True
            except Exception as e:
                print("SSH2登陆错误：", e)
                self.olt_LinkState = False
                self.logQueue.put("SSH2登录失败,请检查IP地址，用户名密码是否正确，确认无误后请重新登录")
                return False
        else:
            print("login_method值传递错误")
            #QtWidgets.QMessageBox.critical(self, u"网络连接检查", u"请检查配置网络是否连接正常，确认无误后请重新操作")
            return False

    # 清除
    @pyqtSlot()
    def on_pushButton_clear_clicked(self):
        """
        Slot documentation goes here.
        """
        self.lineEdit_model.clear()
        self.lineEdit_customer.clear()
        self.lineEdit_user.clear()
        self.lineEdit_pwd.clear()
        self.lineEdit_newPasswd.clear()

    # 获取文件路径
    @pyqtSlot()
    def on_pushButton_openPath_clicked(self):
        """
        Slot documentation goes here.
        """
        print("点击选择文件")
        try:
            download_path = QtWidgets.QFileDialog.getOpenFileName(self, u"选择视频文件", "/")
            print(download_path[0])
            self.lineEdit_filePath.clear()
            self.lineEdit_filePath.setText(self._translate("tkDialog", download_path[0]))
        except Exception as e:
            print(e)
    
    @pyqtSlot()
    def on_pushButton_up_clicked(self):
        """
        Slot documentation goes here.
        """
        ip = self.lineEdit_ipAddr.text()
        username = self.lineEdit_username.text()
        passwd = self.lineEdit_passwd.text()
        localPath = self.lineEdit_filePath.text()
        directory = self.comboBox_userList.currentText()
        if ip == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"IP地址不能为空")
            return
        if username == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"用户名不能为空")
            return
        if passwd == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"登陆密码不能为空")
            return
        if directory == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"请在右侧选择需要上传文件的用户")
            return
        if localPath == "":
            warning = QtWidgets.QMessageBox.warning(self, u"提示", u"请选择需要上传的文件")
            return

        self.modifyWidgetState(False)
        self.fileName = localPath.split("/")[-1]

        print("开始上传")
        self.upload = FTPThread(ip, username, passwd, self.fileName, directory, localPath)
        self.upload.start()
        self.upload.sign_to_State.connect(self.uploadFinsh)

    def modifyWidgetState(self, check):
        self.lineEdit_filePath.setEnabled(check)
        self.pushButton_openPath.setEnabled(check)
        self.pushButton_up.setEnabled(check)

    def uploadFinsh(self, check):
        self.modifyWidgetState(True)
        if check:
            information = QtWidgets.QMessageBox.information(self, u"提示", u"上传完成")
            path = "ftp://10.110.30.86/" + self.fileName
            self.label_downloadPath.setText(self._translate("MainWindow", path))
        else:
            warning = QtWidgets.QMessageBox.warning(self, u"警告", u"上传失败，请重试")

class TelnetDev(object):

    def __init__(self):
        self.shell_prompts = ('#', '$', ':~$' )

    def auth(self, host, port, usr, pwd, login_prompt):
        print("开始登陆")
        self.tl = telnetlib.Telnet(host, port)
        self.tl.set_debuglevel(2)
        print("正在加载文件，请稍等……")
        time.sleep(0.5)
        self.tl.read_until(bytes(login_prompt[0],encoding="ascii"))
        self.tl.write(usr.encode("ascii"))
        self.tl.read_until(bytes(login_prompt[1],encoding="ascii"))
        self.tl.write(pwd.encode("ascii"))
        print("登陆成功")

    def exec_cmd(self, cmd):
        self.tl.write(cmd.encode("ascii"))
        time.sleep(1)
    def read_until(self,prompt):
        msg = self.tl.read_until(bytes(prompt, encoding="ascii")).decode("utf-8")
        print("返回msg", msg)
        return msg
    def read_some(self):
        msg = self.tl.read_some().decode("utf-8")
        print("返回msg", msg)
        return msg
    def read_very_eager(self):
        msg = self.tl.read_very_eager().decode("utf-8")
        print("返回msg", msg)
        return msg
    def read_very_lazy(self):
        msg = self.tl.read_very_lazy().decode("utf-8")
        print("返回msg", msg)
        return msg
    def read_all(self):
        msg = self.tl.read_all().decode("utf-8")
        print("返回msg", msg)
        return msg
    def close(self, cmd):
        self.tl.write(cmd.encode("ascii"))


class FTPThread(QtCore.QThread):
    sign_to_State = QtCore.pyqtSignal(bool)

    def __init__(self, ip, username, passwd, fileName, directory, localPath, parent=None):
        super(FTPThread, self).__init__(parent)
        self.ThreadStop = False
        self.ip = ip
        self.username = username
        self.passwd = passwd
        self.fileName = fileName
        self.localPath = localPath
        self.directory = directory

    def run(self):
        # remotePath = "product/" + self.directory + "/" + self.fileName
        # remotePath = remotePath.encode("utf-8").decode("latin1")
        self.fileName = self.fileName.encode("utf-8").decode("latin1")
        print("filename", self.fileName)
        ftp = FTP()
        ftp.set_debuglevel(2)
        ftp.connect(self.ip, 21)
        ftp.login(self.username, self.passwd)
        print(ftp.getwelcome())


        try:
            # 清空目录
            ftp.cwd("product/" + self.directory)
            fileList = ftp.nlst()
            if fileList:
                print("dir", dir)
                for file in fileList:
                    ftp.delete(file)
                fileList = ftp.nlst()
                if not fileList:
                    print("成功清空目录")
            else:
                print("目录为空")

            # 开始上传文件
            bufsize = 1024
            f = open(self.localPath, 'rb')
            ftp.storbinary("STOR " + self.fileName, f, bufsize)
            ftp.set_debuglevel(0)
        except SystemError as e:
            print(e)
            self.sign_to_State.emit(False)
        except Exception as e:
            print(e)
            self.sign_to_State.emit(False)
        finally:
            ftp.close()
        self.sign_to_State.emit(True)


    def stop(self):
        pass

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    splash = QtWidgets.QSplashScreen(QPixmap("pic/logo.jpg"))
    splash.show()
    ui = MainWindow()
    ui.show()
    splash.finish(ui)
    sys.exit(app.exec_())
