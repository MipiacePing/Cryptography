from functools import reduce
import math
import random
import re
import sys
import time
from typing import Counter
S_box = [0x6, 0x4, 0xc, 0x5, 0x0, 0x7, 0x2, 0xe, 0x1, 0xf, 0x3, 0xd, 0x8, 0xa, 0x9, 0xb]
P_box = [0x0, 0x3, 0x8, 0xc, 0x1, 0x5, 0x9, 0xd, 0x2, 0x6, 0xa, 0xe, 0x3, 0x7, 0xb, 0xf]
S_linear_table = [ [-8]*16 for i in range(16)]     # 线性分布表
S_table = S_linear_table
S_linear_table_p = [ [0]*16 for i in range(16)]    # 线性分布概率分布表
S_table_p = S_linear_table_p

def S(in_):
    if in_>0xf:
        out  = S_box[in_&0xf000>>12]<<12
        out += S_box[in_&0x0f00>>8]<<8
        out += S_box[in_&0x00f0>>4]<<4
        out += S_box[in_&0x000f]
        return out
    return S_box[in_]

def S_inv(in_):
    if in_>0xf:
        out  = S_box.index((in_&0xf000)>>12)<<12
        out += S_box.index((in_&0x0f00)>>8)<<8
        out += S_box.index((in_&0x00f0)>>4)<<4
        out += S_box.index(in_&0x000f)
        return out
    return S_box.index(in_)

def P(in_):
    in_ = "{:0>16b}".format(in_)
    #print(in_)
    out = ""
    for i in P_box:
        out += in_[i]
    return int(out,2)

def P_inv(in_):
    in_ = "{:0>16}".format(str(bin(in_))[2:])
    #print(in_)
    out = ""
    for i in range(16):
        out += in_[P_box[i]]
    return int(out,2)

'''计数JiShu，计数num中1的个数'''
def JS(num):  
    count = 0
    while num:
        if num&1:
            count+=1
        num>>=1
    return count%2

'''堆积引理求ε，传入的E是一组概率'''
def Duiji(E): 
    if not E:
        return 0
    if len(E) == 1:
        return E[0]
    result = 0.5
    for p in E:
        result *= 2*p
    return result


'''计算S盒的线性分布表和概率分布表'''
def get_S_linear_table(Abs=0):
    for alpha in range(16):
        for beta in range(16):
            for x in range(16):
                if JS(alpha&x) == JS(beta&S(x)):
                    S_table[alpha][beta]+=1
    for i in range(16):
        for j in range(16):
            if Abs:
                S_table_p[i][j] = abs(S_table[i][j])/16. # 得到加权有向图的邻接矩阵
            else:
                S_table_p[i][j] = S_table[i][j]/16.

'''打印线性分布表'''         
def print_S_linear_table(table=S_linear_table):
    print('\t\t\t\tS盒线性分布表')
    print('α\β\t',end='')
    for i in range(16):
        print(hex(i)[2:],end='\t')
    print()
    for i in range(16):
        print(hex(i)[2:],end='')
        for j in range(16):
            print('{:>4}'.format(table[i][j]),end='')
        print()

'''清空已访问集合的部分位置'''
def clear_visited(begin):  
    for i in range(begin+1,5):
        Visited[i]=[[]for i in range(4)]

''' 函数通过传入的alpha和S盒的线性分布概率表，寻找下一个未访问过的beta并返回四个S盒的堆积概率 '''
def S_linear(alpha,stack_len,pr_=0):
    flag = 1
    loc = [0,0,0,0]     # 记录遍历的起始点，没有也可以 
    while flag:
        re_i = 0        
        reS_out = 0     # 设置了很多标志，因为有多层循环，需要各种控制标志来决定程序的执行流程
        beta = 0        # S(alpha)是一个16bit的整数
        pr_st=[]
        for i in range(4):  # 有四个S盒，从最右边的S盒开始遍历，注意这里的编号，最右的S盒记为S_0
            if re_i:    # 当第i个S盒的所有S_out都已经访问过，就要先寻找第i+1个S盒的下一个元素，再返回到第0个S盒重新遍历
                break
            S_in = (alpha&Mask[i])>>(4*i)    # 取出第i个S盒对应的4bit作为S_in
            for S_out in range(loc[i],16):   # 遍历邻接矩阵，S_out
                tmp = S_table_p[S_in][S_out] # 取出权重(概率)
                #print(Visited[stack_len][i])
                if abs(tmp) > pr_ and S_out not in Visited[stack_len][i]:  # 如果绝对概率大于0.2，并且没有访问过
                    if reS_out:             
                        '''如果设置了reS_out标志，说明第i-1个S盒已经全部访问过了，所以现在是在找第i个S盒的下一个元素，找到之后就把这个元素加入到已访问列表中，
                        因为这个元素对应的所有地位元素都已经访问过了，所以这个元素要被加入已访问队列'''
                        Visited[stack_len][i].append(S_out)
                        loc[i] += 1
                        reS_out = 0
                        re_i = 1    # 找到了未访问的第i个S盒的元素，然后重新从最右的S盒开始遍历
                        break
                    beta += S_out << (4 * i)# 结果out是四个S盒的输出的级联
                    if tmp<0.5:
                        pr_st.append(tmp)
                    if i==3:				# 如果已经遍历到最左的S盒了，就可以返回了
                        return beta, Duiji(pr_st)
                    break
                elif S_out==15:				# 如果遍历到最0xf还没有满足条件的，说明都已经访问过了
                    for k in range(i+1):    # 重置右边S盒的已访问集合和位置信息集合
                        loc[k] = 0
                        Visited[stack_len][k].clear()
                    if i==3:                # 如果是最左的盒子的最后一个元素，说明当前alpha所有可能的S盒的输出都被访问过了
                        return False,0      # 返回false
                    reS_out = 1             # 设置信号reS_out
                    continue

'''寻找比较好的线性特征路径'''
def getgoodpath(S_num):  
    GLP = []    # good linear path
    clear_visited(-1)
    #print_S_linear_table(S_table_p)
    '''预设概率，如果当前栈中的路径堆积概率小于这个值，那就舍弃当前路径，
       主要作用在剪枝，次作用是筛选,因为高概率线性路径本身就是高概率的而不是靠小概率的路径积累出来的'''
    Pr = Duiji([1/16]*4)     
    testset = [0x8000,0x8,0x880,0xd000,0x1000]
    for alpha in testset:
        alpha_tmp = "{:0>4}".format(hex(alpha)[2:])   
        if alpha_tmp.count('0')<2:             # 控制输入线性掩码的非零位置
            continue
        stack = []
        stack.append(alpha)
        flag = 1
        pr_stack = [1]
        while flag:                            # 开始寻找 线性壳头为alpha的所有高概率线性路径
            pathpr = 0                         # 储存当前栈上的路径的概率乘积，需要使用堆积引理
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
            '''核心函数，stack[-1]是栈顶元素，函数返回下一个alpha过S盒后的beta,以及概率p'''
            beta,pr = S_linear(stack[-1],len(stack),pr_=0)    

            if beta:  # 如果有beta输出
                pr_stack.append(pr)                 # 将概率压栈
                pathpr = Duiji(pr_stack[1:])        # 计算当前路径的概率乘积，可能是一个负数
                if abs(pathpr) > Pr:                # 如果当前路径的绝对概率已经小于一个预设值Pr，那么就抛弃当前路径，也是剪枝的思想
                    stack.append(P(beta))           # 如果概率比预设Pr大，就压入栈
                else:                       
                    pr_stack.pop()                  # 弹出栈顶元素的概率
                    tmp = P_inv(stack.pop()) & 0x000f  #加入到栈顶的是P置换之后的元素，需要经过逆置换再加入Visited
                    pr_stack.pop()                  # stack.pop()之后一定要跟一个pr.pop

                    '''更新已访问集合，把弹出的栈顶元素的最后一个位置加入已访问，在S_diff函数中就可以避免重复访问或漏掉元素'''
                    Visited[len(stack)][0].append(tmp)
                    clear_visited(len(stack))       # 清空栈高位的已访问集合，因为栈底层的元素变动了，所以栈顶方向的元素需要重新遍历
            else:       
                '''如果当前栈顶元素alpha的所有beta都已经遍历过了，返回值就是False，进入else，栈弹出一个元素，相当于回退'''
                tmp = P_inv(stack.pop())&0x000f
                pr_stack.pop()
                Visited[len(stack)][0].append(tmp)
                clear_visited(len(stack))           # 同上述作用

            if len(stack)==R+1:             
                '''栈的长度已经达到R轮加密的要求，可以加入GLP，同时将当前栈顶元素的最后4bit加入相应的已访问队列'''
                str_beta = "{:0>4}".format(hex(P(beta))[2:])
                if str_beta.count('0') > 1 and str_beta[S_num] != '0': 
                    GLP.append((stack[:],pathpr))   # 这里还要筛选一下beta，去除beta中第S_num个S盒为0的输出掩码

                tmp = beta & 0x000f
                Visited[-1][0].append(tmp)  # 更新已访问集合，
                stack.pop() 
                pr_stack.pop()

            elif len(stack)==0:             # 如果当前alpha的所有路径都已经访问过了，栈就会回退为空，然后我们结束while
                flag=0

    # 统计线性壳特征
    linear_pr = dict()
    for path in GLP:
        alpha,beta,pr_ = path[0][0],path[0][-1],path[-1]
        tmp = linear_pr.get((alpha,beta))
        if tmp:
            linear_pr[(alpha,beta)] += pr_
        else:
            linear_pr[(alpha,beta)] = pr_
    path_order = sorted(linear_pr.items(), key=lambda x: abs(x[1]),reverse=True)
    
    # alpha,beta = 0x8000,0x300  # 查看某族线性壳的具体路径
    # count = 0
    # for path in GLP:
    #     if path[0][0] == alpha and path[0][-1] == beta:
    #         print(path)
    #         count += 1
    # print(count)

    k = 10
    print("\n-------------从左向右，第{}个S盒高概率线性路径共{}条，最优的{}个线性壳如下-------------".format(S_num+1,len(GLP),k))
    i=0
    for item in path_order:
        print("α={}，β={}，Pr={}".format(hex(item[0][0]),hex(item[0][1]),item[-1]))
        i += 1
        if i>k:
            break
    return list(path_order[0])


def task1(n=8):   # n代表明文量的系数
    # path=（α，β，ε）
    goodpath = [[0xd000,0x4000,0.046875], # 左边第一个盒子最好的线性壳 

                [0x8000,0x400,0.046875],  # 左边第2个盒子表现最好的线性壳 

                [0x1000,0x4040,0.0390625],  # 1111101    左数第3个S盒，效果较好的2个线性壳,也需要0x8500的帮助
                [0x8000,0x1010,0.0390625],  # 0011101  

                [0xd000,0x4,0.0625],        # 111111  最右边的盒子表现较好的3个线性壳，需要0x8500的帮助
                [0x880,0x4004,0.048828125], # 111111
                [0x8,0x404,-0.04736328125],     # good
                [0x8000,0x404,-0.0936279296875],   # good
                ]

    for path in goodpath:
        print()
        alpha,beta,e = path
        print("α={}，β={}，ε={}".format(hex(alpha),hex(beta),e))
        if beta in [0x4004,0x4,0x404,0x8,0x504,0x4008,0x44]:  # 多跑几次，可以确定最后一个盒子是e的概率最大
            N = math.ceil(n*abs(e)**(-2))
            P_random = random.sample(list(range(65536)),N)
            P_C = []
            for p in P_random:
                P_C.append((p,int(ciphertext[p],16)))
            print("明文量={}".format(len(P_C)))
            K5_num = 16
            T = [int(-N/2)]*K5_num
            for k5_3 in range(K5_num):
                tmp = 0x8500+k5_3        # 在确定完0x8500之后来统计的
                for p,c in P_C:
                    if JS(p&alpha)^JS(S_inv(c^tmp)&beta)==0:
                        T[k5_3]+=1

            print("计数器中最高的5个密钥：\n密钥\t计数")
            k5_order = sorted(T,key=lambda x:abs(x),reverse=True)
            for i in range(5):
                print("0x{}\t{}".format(hex(T.index(k5_order[i]))[2:],k5_order[i]))
            print("最大可能的秘钥是：0x{}".format(hex(T.index(k5_order[0]))[2:]))
           
        elif beta == 0x400:  # 可以确定左边第二个盒子是5
            N = math.ceil(n*abs(e)**(-2))
            P_random = random.sample(list(range(65536)),N)
            P_C = []
            for p in P_random:
                P_C.append((p,int(ciphertext[p],16)))
            print("明文量={}".format(len(P_C)))
            K5_num = 16
            T = [int(-N/2)]*K5_num
            for k5_1 in range(K5_num):
                tmp = k5_1<<8
                for p,c in P_C:
                    if JS(p&alpha)^JS(S_inv(c^tmp)&beta)==0:
                        T[k5_1]+=1           
            print("计数器中最高的5个密钥：\n密钥\t计数")
            k5_order = sorted(T,key=lambda x:abs(x),reverse=True)
            for i in range(5):
                print("0x{}00\t{}".format(hex(T.index(k5_order[i]))[2:],k5_order[i]))
            print("最大可能的秘钥是：0x0{}00".format(hex(T.index(k5_order[0]))[2:]))
       
        elif beta in [0x4000,0x8000,0x1000]: #可以确定最左边的盒子是8，
            N = math.ceil(n*abs(e)**(-2))
            P_random = random.sample(list(range(65536)),N)
            P_C = []
            for p in P_random:
                P_C.append((p,int(ciphertext[p],16)))
            print("明文量={}".format(len(P_C)))
            T = [int(-N/2)]*16
            for k5_0 in range(16):
                tmp = (k5_0<<12)
                for p,c in P_C:
                    if JS(p&alpha)^JS(S_inv(c^tmp)&beta)==0:
                        T[k5_0]+=1           
            print("计数器中最高的5个密钥：\n密钥\t计数")
            k5_order = sorted(T,key=lambda x:abs(x),reverse=True)
            for i in range(5):
                print("0x{}000\t{}".format(hex(T.index(k5_order[i]))[2:],k5_order[i])) 
            print("最大可能的秘钥是：0x{}000".format(hex(T.index(k5_order[0]))[2:]))    
       
        if beta in [0x4040,0x1010,0x44,0x440,0x10]:
            N = math.ceil(n*abs(e)**(-2))
            P_random = random.sample(list(range(65536)),N)
            P_C = []
            for p in P_random:
                P_C.append((p,int(ciphertext[p],16)))
            print("明文量={}".format(len(P_C)))
            T = [0]*16
            for k5_2 in range(16):
                tmp = 0x8500+(k5_2<<4)   # 在确定完0x8500之后来统计的
                for p,c in P_C:
                    if JS(p&alpha)^JS(S_inv(c^tmp)&beta)==0:
                        T[k5_2]+=1      
            print("计数器中最高的5个密钥：\n密钥\t计数")
            k5_order = sorted(T,key=lambda x:abs(x),reverse=True)
            for i in range(5):
                print("0x{}0\t{}".format(hex(T.index(k5_order[i]))[2:],k5_order[i]))          
            print("最大可能的秘钥是：0x{}0".format(hex(T.index(k5_order[0]))[2:]))

'''
    0->0   1->1   1*->2    2*->3   ?->4
'''
def cheng(a,b): #b的值域是 0，1，1F；a的值域是0,1,2,3,4
    if b==0:
        return 0
    if b==1:
        return a
    if b==0xf:
        if a==0 or a==1 or a==4:
            return a
        if a==2:
            return 1    # 1*+1F =1
        if a==3:
            return 4    # 2*+1F =2=？
def jia(a,b): 
    tmp = a+b
    if tmp>=4 or a==b==1:
        return 4
    return tmp      

def dot(in_,matrix):
    num = len(in_)
    if num!= len(matrix):
        return IndexError
    out_ = []
    for j in range(len(matrix[0])):
        tmp = 0
        for i in range(num):
            tmp = jia(cheng(in_[i],matrix[i][j]),tmp)
        out_.append(tmp)
    return tuple(out_)

def Conflict(a,b):
    conflict_set = [[1,2],[0],[0,3],[2],[]] # 下标对应 0 1 1* 2* ？
    for i in range(len(a)):
        if b[i] in conflict_set[a[i]]:
            return True
    return False

trans_map = {0:'0',1:'1',2:'1*',3:'2*',4:'?'}
def trans(in_):
    out = []
    for i in range(len(in_)):
        out.append(trans_map[in_[i]])
    return tuple(out)

def get_Longest_path(forward_path,back_path):
    '''遍历，找出所有的矛盾级联'''
    Longest_path = []
    longest = 0
    for f_path in forward_path:		# 遍历正向路径
        tmp_f = []
        for f in range(len(f_path)):	# 在正向路径的f位置，遍历逆向路径
            tmp_f.append(trans(f_path[f]))
            for b_path in back_path:
                tmp_b = []
                '''遍历逆向路径主要就是找轮数和判断冲突'''
                for b in range(len(b_path)): 
                    tmp_b.append(trans(b_path[b]))
                    long = f+b
                    if long >= longest:
                        '''如果当前长度超过最长的，再判断是否矛盾'''
                        if Conflict(f_path[f],b_path[b]): 
                            if long > longest:
                                longest = long
                                '''如果有更长的矛盾路径，那么就重置最长路径'''
                                Longest_path.clear()
                            if [tmp_f,tmp_b] not in Longest_path:
                                '''一样长的矛盾路径，记录下来'''
                                Longest_path.append([tmp_f[:],tmp_b[:]])
                            continue
    print("最长的轮数为{},零相关线性路径共有{}条".format(longest,len(Longest_path)))
    for i in range(len(Longest_path)):
        print("\n第{}条:".format(i+1))
        print("正向路径:{}".format(Longest_path[i][0]).replace("'",'').replace("), ",")->").replace(", ",","))
        print("逆向路径:{}".format(Longest_path[i][1]).replace("'",'').replace("), ",")->").replace(", ",","))

def task2():
    E_matrix = [[0xf,  0,   0,   1],
                [  1,  0,   0,   0],
                [  0,  1,   0,   0],
                [  0,  0,   1,   0]]

    D_matrix = [[  0,  1,   0,   0],
                [  0,  0,   1,   0],
                [  0,  0,   0,   1],
                [  1,0xf,   0,   0]]                

    linear_set = [0,1,2,3,4] # 对应 0,1,1*,2*,？
    forward_path = []
    back_path = []
    for x0 in linear_set:	# 寻找正向路径
        for x1 in linear_set:
            for x2 in linear_set:
                for x3 in linear_set:
                    tmp = [(x0,x1,x2,x3)]
                    if tmp[0].count(0)+tmp[0].count(4) == 4 :
                        continue
                    while 1:
                        out = dot(tmp[-1],E_matrix)         # 正向路径，用的E矩阵  
                        if out.count(0)+out.count(4) == 4:  # 结束条件 如果四个值只有0和?，比如(0,?,0,?)
                            if len(tmp)>1: 
                                forward_path.append(tmp)
                            break
                        tmp.append(out)
    for y0 in linear_set:	# 寻找反向路径
        for y1 in linear_set:
            for y2 in linear_set:
                for y3 in linear_set:
                    tmp = [(y0,y1,y2,y3)]
                    if tmp[0].count(0)+tmp[0].count(4) == 4 :
                        continue
                    while 1:
                        out = dot(tmp[-1],D_matrix) 	# 反向路径，用的D矩阵  
                        if out.count(0)+out.count(4) == 4: # 结束条件 如果四个值只有0和?，比如(?,?,0,?)
                            if  len(tmp)>1:
                                back_path.append(tmp)
                            break
                        tmp.append(out)
    # for item in forward_path: 
    #     print(item)
    # for item in back_path:
    #     print(item)
    get_Longest_path(forward_path,back_path) # 寻找最长零相关线性路径，和广义的一样


if __name__=="__main__":
    fp = open("cipher_6.txt")
    ciphertext = re.findall("0x[0-9a-f]+",fp.read())
    Mask = [0x000f,0x00f0,0x0f00,0xf000]
    R = 4
    Visited = [[[] for i in range(4)] for i in range(R + 1)]
    get_S_linear_table(Abs = 0)
    print_S_linear_table()
    print_S_linear_table(S_linear_table_p)

    start = time.time()
    print("-------------------------------------Task1-------------------------------------")
    task1(8)
    print("task1 costs {}s".format(time.time()-start))

    # s_num = int(input("请输入要寻找的S盒的线性特征（从左到右编号为1-4）："))
    # if s_num in [1,2,3,4]:
    #     getgoodpath(s_num-1)

    # start = time.time()
    # print("-------------------------------------Task2-------------------------------------")
    # task2()
    # print("task2 costs {}s".format(time.time()-start))
