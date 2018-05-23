msg = """cat /etc/vsftpd/vuser_list
NTB-500H_BinZhou
500h111111110
NTB-500H_WeiFang
00000000
-bash-4.2$ """

tmpList = msg.split('\r\n')
tmpList = tmpList[1:]
tmpList = tmpList[:-1]
print(tmpList)
userList = []
n = 0
while n < len(tmpList):
    userList.append(tmpList[n])
    n += 2
print(userList)


msg = "cat /etc/vsftpd/vuser_list"

msg