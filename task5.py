from functools import reduce
import numpy
import sys
S_box = [0x6, 0x4, 0xc, 0x5, 0x0, 0x7, 0x2, 0xe, 0x1, 0xf, 0x3, 0xd, 0x8, 0xa, 0x9, 0xb]
P_box = [0x0, 0x4, 0x8, 0xc, 0x1, 0x5, 0x9, 0xd, 0x2, 0x6, 0xa, 0xe, 0x3, 0x7, 0xb, 0xf]
S_table = [[0]*16 for i in range(16)]

def S(in_):
    if in_>0x000f:
        out = S_box[in_&0xf000>>12]<<12
        out += S_box[in_&0x0f00>>8]<<8
        out += S_box[in_&0x00f0>>4]<<4
        out += S_box[in_&0x000f]
        return out
    return S_box[in_]

def P(in_):
    in_ = "{:0>16}".format(str(bin(in_))[2:])
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

'''S_3 S_2 S_1 S_0'''

def S_diff(inxor,stack_len):
    ''' 函数通过传入的inxor和S盒的差分分布表（邻接矩阵），寻找下一个未访问过的S(inxor)并返回其概率 '''
    pr = 1
    flag = 1
    loc = [0,0,0,0]     # 记录遍历的起始点，没有也可以 
    while flag:
        re_i = 0        
        reS_out = 0     # 设置了很多标志，因为有多层循环，需要各种控制标志来决定程序的执行流程
        out = 0         # S(inxor)是一个16bit的整数
        pr=1            
        for i in range(4):  # 有四个S盒，从最右边的S盒开始遍历，注意这里的编号，最右的S盒记为S_0
            if re_i:    # 当第i个S盒的所有S_out都已经访问过，就要先寻找第i+1个S盒的下一个元素，再返回到第0个S盒重新遍历
                break
            S_in = (inxor&Mask[i])>>(4*i)   # 取出第i个S盒对应的4bit作为S_in
            for S_out in range(loc[i],16):  # 遍历邻接矩阵，S_out
                tmp = S_table[S_in][S_out]  # 取出权重(概率)
                #print(Visited[stack_len][i])
                if tmp > 0 and S_out not in Visited[stack_len][i]:  # 如果概率大于0，并且没有访问过
                    if reS_out:             
                        '''如果设置了reS_out标志，说明第i-1个S盒已经全部访问过了，所以现在是在找第i个S盒的下一个元素，
                           找到之后就把这个元素加入到已访问列表中，'''
                        Visited[stack_len][i].append(S_out)
                        loc[i] += 1
                        reS_out = 0
                        re_i = 1    # 找到了未访问的第i个S盒的元素，然后重新从最右的S盒开始遍历
                        break
                    out += S_out << (4 * i)	# 结果out是四个S盒的输出的级联
                    pr *= tmp				# 概率是四个S盒的概率积
                    if i==3:				# 如果已经遍历到最左的S盒了，就可
                        return out, pr
                    break
                elif S_out==15:				# 如果遍历到最0xf还没有满足条件的，说明都已经访问过了
                    for k in range(i+1):    # 重置右边S盒的已访问集合和位置信息集合
                        loc[k] = 0
                        Visited[stack_len][k].clear()
                    if i==3:                # 如果是最左的盒子的最后一个元素，说明当前inxor所有可能的S盒的输出都被访问过了
                        return False,0      # 返回false
                    reS_out = 1             # 设置信号reS_out
                    continue

'''清空已访问集合的部分位置'''
def clear_visited(begin):
    for i in range(begin+1,5):
        Visited[i]=[[]for i in range(4)]

# 通过S盒线性分布表，利用DFS，构造N轮加密，一定条件下的所有高概率差分路径并找到高概率差分特征
def task5_new(S_num):
    GDP = []    # good differ path 好的差分路径，hhh，再叫best就不好了

    '''计算S差分分布表,并将每个位置都除16,就是一张加权的有向图'''
    for i in range(16):
        for j in range(16):
            inxor = i ^ j
            outxor = S(i) ^ S(j)
            S_table[inxor][outxor] += 1
    for i in range(16):
        for j in range(16):
            S_table[i][j] /= 16.

    '''打印S盒异或表'''
    # for item in S_table:
    #     print(item)
    #print(S_diff(0x0001,[1,1,1,1],4))

    #testset = [0x0002,0x0001,0x0020,0x0010] # 用于固定要查找的输入异或

    testset = [0x0500]
    for inxor in range(1,65536):            # 遍历输入差分
        str_xor = "{:0>4}".format(hex(inxor)[2:])   
        if str_xor.count('0')<2:            # 输入差分至少有两个S盒为0，剪枝，去掉低概率路径
            continue
        # if inxor not in testset:          # 通过固定输入差分到testset测试代码正确性
        #     continue
        stack = []                          # DFS深度优先遍历用到的栈结构
        stack.append(inxor)                     
        flag = 1                            # 当栈为空，flag置0，压入下一个输入异或的路径
        pr_stack = [1]                      # 计算概率的乘积，在栈底留一个元素，防止空列表pop错误
        while flag:                         # 开始寻找 inxor对应的所有高概率差分路径
            pathpr=0                        # 储存当前栈上的路径的概率乘积

            '''核心函数，stack[-1]是栈顶元素，函数返回下一个outxor = S(stack[-1]),以及 pr = Pr(S(stack[-1])->outxor)'''
            outxor,pr = S_diff(stack[-1],len(stack))    

            if outxor:  # 如果有outxor输出
                pr_stack.append(pr)         # 概率压栈
                pathpr = reduce(lambda x,y:x*y,pr_stack)    # 计算当前路径的概率乘积
                if pathpr > Pr:             # 如果当前路径的概率已经小于一个预设值Pr，那么就抛弃当前路径，也是剪枝的思想
                        stack.append(P(outxor)) # 如果概率比预设Pr大，就压入栈
                else:                       
                    
                    pr_stack.pop()          # 弹出栈顶元素的概率
                    tmp = P_inv(stack.pop()) & 0x000f  #加入到栈顶的是P置换之后的元素，需要经过逆置换再加入Visited
                    pr_stack.pop()          # stack.pop()之后一定要跟一个pr.pop

                    '''更新已访问集合，把弹出的栈顶元素的最后一个位置加入已访问，在S_diff函数中就可以避免重复访问或漏掉元素'''
                    Visited[len(stack)][0].append(tmp)
                    clear_visited(len(stack)) # 清空栈高位的已访问集合，因为栈底层的元素变动了，所以栈顶方向的元素需要重新遍历
            else:       
                '''如果当前栈顶元素inxor的所有S(inxor)都已经遍历过了，返回值就是False，进入else，栈弹出一个元素，相当于回退'''
                tmp = P_inv(stack.pop())&0x000f
                pr_stack.pop()
                Visited[len(stack)][0].append(tmp)
                clear_visited(len(stack))     # 同上述作用

            if len(stack)==R+1:             
                '''栈的长度已经达到R轮加密的要求，可以加入BDP，同时将当前栈顶元素的最后4bit加入相应的已访问队列'''
                str_outxor = "{:0>4}".format(hex(P(outxor))[2:])
                if str_outxor.count('0') > 1 and str_outxor[S_num] != '0': 
                    GDP.append((stack[:],pathpr)) # 这里还要筛选一下输出异或，去除输出异或中第S_num个S盒为0的输出差分

                tmp = outxor & 0x000f
                Visited[-1][0].append(tmp)  # 更新已访问集合，
                stack.pop() 
                pr_stack.pop()

            elif len(stack)==0:             # 如果当前输异或inxor的所有路径都已经访问过了，栈就会回退为空，然后我们结束while
                flag=0

    print("\n从左向右第{}个S盒的高概率差分路径共{}条".format(S_num+1,len(GDP)))

    # print("\n---------------最优差分路径---------------\n")
    # for path in GDP:
    #     for i in range(5):
    #         print(hex(path[0][i]),end=" ")
    #     print(path[-1])

    # 统计差分特征
    diff_pr = dict()
    for path in GDP:
        inxor,outxor,pr_ = hex(path[0][0]),hex(path[0][-1]),path[-1]
        tmp = diff_pr.get((inxor,outxor))
        if tmp:
            diff_pr[(inxor,outxor)] += pr_
        else:
            diff_pr[(inxor,outxor)] = pr_
    d_order = sorted(diff_pr.items(), key=lambda x: x[1],reverse=True)

    print("\n---------------从左向右，第{}个S盒最优的10个差分特征---------------\n".format(S_num+1))
    for i in range(10):
        print(d_order[i])

# 构造R轮差分的最优差分路径
def task5(R=4):
    # 一轮差分有向图的邻接矩阵，下标0,1,2,3分别对应0001,0002,0010,0020,行表示行标的出度，列表示列表的入度，
    mymap = {0:"0x0001", 1:"0x0002", 2:"0x0010", 3:"0x0020"}
    Adjacency_Matrix = [[0, 0, 1, 0],        
                        [1, 0, 1, 0],
                        [0, 0, 0, 1],
                        [0, 1, 0, 1]]
    visited = [[]for i in range(R+1)] # 已访问元素列表，对5个位置都要记录已访问列表
    BDP = []    # 最优差分路径 Best Diff Path
    flag = 1
    for i in range(4):
        stack = []  # 栈，用于遍历邻接矩阵
        stack.append(i)
        j=0
        flag = 1
        while flag:
            if Adjacency_Matrix[stack[-1]][j]==1 and j not in visited[len(stack)]: # 有向图需要更改遍历的行
                stack.append(j)
                j=0
            else:
                j+=1
            if len(stack)==R+1:
                BDP.append(stack[:])               # 路径长度满足要求，添加到BDP中，
                visited[-1].append(stack.pop()) # 长度为5，所以要把栈顶元素加入到下标4的visited列表中
            elif j==4:  # 到达行的末尾，说明当前栈不可能继续增长，需要回退
                visited[len(stack)].clear() # 先把visited[len(stack)]列表清空，
                tmp = stack.pop()           # 然后弹出栈顶元素，
                visited[len(stack)].append(tmp) # 再把栈顶元素加入到
                j=0     # 从头遍历
            if not stack:
                flag=0

    print("---------------最优差分路径---------------")
    print("\n{}轮最优差分路径共{}条，概率均为{}".format(R,len(BDP),pow(6./16,R)))
    for path in BDP:
        for item in path:
            print(mymap[item],end=" -> ")
        print("\b\b\b   ")

    print("\n---------------最优差分特征---------------\n")
    for i in range(4):
        rank = [0]*4
        #print("输出差分为{}".format(mymap[i]))
        for path in BDP:
            if path[-1] == i:
                rank[path[0]]+=1
                # for item in path:
                #     print(mymap[item],end=" -> ")
                # print("\b\b\b   ")
        for j in range(4):
            if rank[j]!=0:
                print("输入差分:{}——>输出差分:{} 共有{}条路径".format(mymap[j],mymap[i],rank[j]))
        print()


if __name__=="__main__":
    R=4     # R轮加密的差分特征
    Visited = [[[] for i in range(4)] for i in range(R + 1)]
    Mask = [0x000f,0x00f0,0x0f00,0xf000]
    Pr = pow(2/16.0,6)
    Pr=0.00024
    #print(P(0x0010),P_inv(0x0002))
    #task5()
    # 有个bug，连着跑互相会影响，应该是python可变变量的问题，不想改了，只能多跑几次了
    s_num = int(input("请输入要寻找的S盒的差分特征（从左到右编号为1-4）："))
    if s_num in [1,2,3,4]:
        task5_new(s_num-1)
    