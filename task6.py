import random

S=[6,4,12,5,0,7,2,14,1,15,3,13,8,10,9,11]

#提取数据并处理
fp=open('cipher_6.txt','r')
data=fp.read()
cipher=data.split(',')
#print(cipher[0])
cipher[0]=cipher[0][-6:]    #第一个元素是  char cipher[] = {0xc406 所以只需要后面6个字符即可
cipher.pop()    #最后一个元素是  ,}  所以需要删除
for i in range(len(cipher)):
    cipher[i] = cipher[i][2:]   #将0x去掉


#随机取明密文对，用输出差分值做索引，输入对i和j做元素
def get_pc(num,xor):
    p_c={}
    for i in range(0xffff):
        p_c[i]=[]       #输出差分值作为索引
    count=0
    while(count<num):
        i=random.randint(0,0xffff)
        j=i^xor
        if j>i:     #保证不会出现取(i,j)与(j,i)
            c1_xor_c2=int(cipher[i],16)^int(cipher[j],16)   #输出差分值
            p_c[c1_xor_c2].append([i,j])    #输出差分值做索引，输入差分对做元素
            count+=1
    for i in range(0xffff):     #删除空列表
        if p_c[i]==[]:
            del(p_c[i])
    #print(p_c)
    return p_c

#去噪
def delpc(p_c,s_num,res_5,xor_out,K5=0x0000):     #s_num是第几个盒子不为0，如0020就是第3个不为0，res_5是经过第5轮后的输出差分可能的结果
    dellist=[]
    l=len(s_num)
    mask=[0 for i in range(l)]
    s_mask=0
    for i in range(l):
        mask[i]=0xf000>>((s_num[i]-1)*4)
        s_mask+=mask[i]
        for key in p_c:
            if (key&mask[i])>>((4-s_num[i])*4) not in res_5[i]:    #不在固定的列表里的如b不在[1,2,,9,a]里的
                dellist.append(key)
        #其余位数不等于0的
    s_mask1=s_mask^0xffff
    for key in p_c:
        if key&s_mask1!=0:
            dellist.append(key)
    if K5:
        for key in p_c:
            for m in p_c[key]:
                c1 = int(cipher[m[0]],16)
                c2 = int(cipher[m[1]],16)
            if S.index((c1&0x00f0^(K5&0x00f0))>>4)^S.index((c2&0x00f0^(K5&0x00f0))>>4) != (xor_out&0x00f0)>>4:
                dellist.append(key)
    dellist=list(set(dellist))
    for i in dellist:   #删除不满足条件的
        del(p_c[i])
    

    res=[]
    for key in p_c:     #将满足条件的所有的明文对整合到一起  由{0:[[x1,x2],[x3,x4]],1:[[y1,y2],[y3,y4]]}变为[[x1,x2],[x3,x4],[y1,y2],[y3,y4]]
        for i in p_c[key]:
            res.append(i)
    return res

#求每一个key的count
def getKey(num,xor_in,xor_out,s_num,res_5,K5=0x0000):     #num是选择明文对数量，xor是输入差分，s_num是第几个s盒输入差分不为0，res_5是经过第5轮后可能的结果
    #K5=0x0090
    p_c=get_pc(num,xor_in)
    after_del=delpc(p_c,s_num,res_5,xor_out,K5)
    #print(len(after_del))
    for i in range(len(s_num)):
        if K5&(0xf000>>((s_num[i]-1)*4))==0:
            value=xor_out>>((4-s_num[i])*4)
            #p_c=get_pc(num,xor_in)
            key={}
            for j in range(2**4):   #初始化所有的密钥的count为0
                key[j]=0

            #K5 = 0x0090
            '''after_del=delpc(p_c,s_num,res_5,xor_out,K5)
            print(len(after_del))'''
            for j in after_del:
                c1=int(cipher[j[0]][s_num[i]-1],16)      #由以上的明文对得到int型密文对
                c2=int(cipher[j[1]][s_num[i]-1],16)
                for k in range(16):
                    x1=c1^k
                    x2=c2^k
                    if S.index(x1)^S.index(x2)==value:
                        key[k]+=1
            res=[]
            maxcount=0
            for k in key:
                if key[k]>maxcount:
                    res=[]
                    res.append(k)
                    maxcount=key[k]
                elif key[k]==maxcount:
                    res.append(k)
    return res



K52=getKey(10000,0x0020,0x0020,[3],[[1,2,9,0xa]],0)
K53=getKey(10000,0x0002,0x0002,[4],[[1,2,9,0xa]],0)
K50=getKey(10000,0x0020,0x2002,[1],[[1,2,9,0xa]],0)


K51=getKey(100000,0x0600,0x0660,[2,3],[[2,4,7,8,0xa,0xb,0xc],[2,4,7,8,0xa,0xb,0xc]],K52[0]<<4)


print('密钥K50为：{0}'.format(K50))
print('密钥K51为：{0}'.format(K51))
print('密钥K52为：{0}'.format(K52))
print('密钥K53为：{0}'.format(K53))

def RoS(num1,num2):     #num1为测试总次数，num2为选取明文对数
    count=0
    for i in range(num1):
        K52=getKey(num2,0x0020,0x0020,[3],[[1,2,9,0xa]],0)
        if len(K52)==1 and K52[0]==9:
            count+=1
    return count/num1
#print('选取100个明文对时成功概率为：{0}'.format(RoS(1000,100)))
#print('选取100个明文对时成功概率为：{0}'.format(RoS(1000,500)))

