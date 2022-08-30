import time
#已经通过计算得到的正向和反向路径
maodun={'0':['1','1*'],'1':['0'],'1*':['0','1*','2*'],'2*':['1*'],'3':[]}
res1=[]
res2=[]
pos=[]
MAX=19
#计算正向和方向路径的函数
class jisuanlujing():
    RES1={}#存储正向传播的字典
    RES2={}#存储反向传播的字典
    E=[['0','0','0','1'],['1','0','0','F'],['0','1','0','0'],['0','0','1','0']]#正向矩阵
    D=[['F','1','0','0'],['0','0','1','0'],['0','0','0','1'],['1','0','0','0']]#反向矩阵
    def xor(self,x,y):#['0','1','1*','2*','3']
        if x=='0':
            return y
        elif y=='0':
            return x
        elif x=='1' and y=='1*':
            return '2*'
        elif x=='1*' and y=='1':
            return '2*'
        else:
            return '3'
    def dot(self,x,G):
        res=[]
        for i in range(4):
            temp=[]
            for j in range(4):
                if G[j][i]=='1':
                    temp.append(x[j])
                elif G[j][i]=='0':
                    temp.append('0')
                else:
                    if x[j]=='1*':
                        temp.append('1')
                    elif x[j]=='2*':
                        temp.append('3')
                    else:
                        temp.append(x[j])
            res.append(self.xor(self.xor(temp[0],temp[1]),self.xor(temp[2],temp[3])))
        return res
    def jisuan(self):
        for x0 in ['0','1','1*','2*','3']:
            for x1 in ['0', '1', '1*', '2*', '3']:
                for x2 in ['0', '1', '1*', '2*', '3']:
                    for x3 in ['0', '1', '1*', '2*', '3']:
                        if x0=='0' and x1=='0' and x2=='0' and x3=='0':
                            continue
                        if x0=='3' and x1=='3' and x2=='3' and x3=='3':
                            break
                        x=[x0,x1,x2,x3]#正向
                        res1=[]
                        res1.append(x)
                        while True:
                            x_=self.dot(x,self.E)
                            if x_==x:
                                break
                            x=x_
                            res1.append(x_)
                        y=[x0,x1,x2,x3]#反向
                        res2=[]
                        res2.append(y)
                        while True:
                            y_=self.dot(y,self.D)
                            if y_==y:
                                break
                            y=y_
                            res2.append(y_)
                        self.RES1['{0},{1},{2},{3}'.format(x0,x1,x2,x3)] = res1
                        self.RES2['{0},{1},{2},{3}'.format(x0,x1,x2,x3)] = res2
start=time.time()
lxg=jisuanlujing()
lxg.jisuan()
#寻找矛盾
for a in lxg.RES1.keys():
    for b in lxg.RES2.keys():
        x=lxg.RES1[a]
        y=lxg.RES2[b]
        l1=len(x)
        l2=len(y)
        for i in range(1,l1):
            for j in range(1,l2):
                if (y[j][0] in maodun[x[i][0]]) or (y[j][1] in maodun[x[i][1]]) or (y[j][2] in maodun[x[i][2]]) or (y[j][3] in maodun[x[i][3]]):
                    if i+j>=MAX:
                        res1.append(x[0:i + 1])
                        res2.append(y[0:j + 1])
                        pos.append([i, j, i + j])
end=time.time()
#统计线性壳
print('Use times:',end-start,'s')
a=[];b=[]
for i in range(len(res1)):
    a.append(res1[i][0])
    b.append(res2[i][0])
for i in range(len(a)-1,0,-1):
    if a[i]==a[i-1] and b[i]==b[i-1]:
        a.pop(i)
        b.pop(i)
print('Total differential path:',len(res1))
print('Total differential:',len(a))
#输出线性壳
for i in range(len(a)):
    print('输入差分:',a[i],'输出差分:',b[i])
#输出线性路径
for i in range(len(res1)):
    print('总轮数:', pos[i][2], '正向轮数:', pos[i][0], '反向轮数:', pos[i][1], '正向路径(最后为矛盾处):', res1[i], '反向路径(开始为矛盾处):',res2[i][::-1])
input()