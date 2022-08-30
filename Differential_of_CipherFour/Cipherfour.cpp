#include <iostream>
#include <cstring>
#include <vector>
#include <algorithm>
#include <time.h>
#include <fstream>
using namespace std;
typedef unsigned short u_short;

u_short S_box[16] = {0x6, 0x4, 0xc, 0x5, 0x0, 0x7, 0x2, 0xe, 0x1, 0xf, 0x3, 0xd, 0x8, 0xa, 0x9, 0xb};
u_short P_box[16] = {0x0, 0x4, 0x8, 0xc, 0x1, 0x5, 0x9, 0xd, 0x2, 0x6, 0xa, 0xe, 0x3, 0x7, 0xb, 0xf};
u_short S_table[0xf][0xf] = {}; //S盒差分表，S[inxor][outxor]，初始化为0
u_short mask[4] = {0x000f, 0x00f0, 0x0f00, 0xf000}; //使用mask的方式进行4bit分组

//输入是16bit的int，输出也是16bit的int
u_short S(u_short in)
{
    if(in<0x10)
        return S_box[in];
    u_short out = 0;
    for (int i = 0; i < 4; i++)
    {
        out += S_box[(in & mask[i]) >> (4 * i)] << (4 * i); //过S盒
    }
    return out;
}

//输入是16bit的int，输出也是16bit的int
u_short P(u_short in)
{
    u_short out = 0;
    for (int i = 0; i < 16; i++)
    {
        auto tmp = P_box[i] - i;
        if (tmp >= 0)
            out += (in & (0x8000 >> P_box[i])) << tmp;        //如果P_box[i]-i>0，就需要左移绝对值位
        else
            out += (in & (0x8000 >> P_box[i])) >> (-1 * tmp); //如果P_box[i]-i<0，就需要右移绝对值位
        //printf("%x\n",out);
    }
    return out;
}

u_short *KeyGen(int R)
{
    //srand(0);
    R += 1; //R轮加密需要R+1个密钥
    u_short *Key = new u_short[R];
    for (int i = 0; i <= R; i++)
    {
        Key[i] = rand() & 0xffff;
    }
    return Key;
}

void KeyGen(int R, int num, u_short **Key) //R轮加密，总共需要num组 Key[num][R+1]
{
    R += 1; //R轮加密需要R+1个密钥
    for (int i = 0; i < num; i++)
    {
        for (int j = 0; j <= R; j++)
            Key[i][j] = rand() & 0xffff;
    }
}

u_short cipherfour(u_short m, int R, u_short *K = NULL) //R轮的Cipherfour算法
{
    if (K == NULL)      //如果给的是NULL，那就随机生成一组秘钥
        u_short *K = KeyGen(R);
    u_short c = m;
    for (int i = 0; i < R; i++)
    {
        c = P(S(c ^ K[i]));
    }
    c ^= K[R]; //异或最后一个密钥
    return c;
}
//函数指针重命名，使用CF代替cipherfour，但是必须提供K的参数
u_short (*CF)(u_short, int, u_short *) = &cipherfour;

void task2(int Keyset_num = 20) //遍历x in {0,1}^16，统计 cipherfour(x)^cipherfour(x^0x00f0)
{
    printf("————————————————task2————————————————\n");
    int R = 4;
    //使用动态二维数组
    u_short **Key = new u_short *[Keyset_num];
    for (int i = 0; i < Keyset_num; i++)
    {
        Key[i] = new u_short[5];
    }
    //固定一组秘钥
    //u_short k[5] = {0x5b92,0x064b,0x1e03,0xa55f,0xecbd};
    // u_short k[5] = {0x3e34, 0xe3de, 0xe12d, 0x78be, 0x5bbd};
    // memcpy(Key[0],k,sizeof(u_short)*(R+1));
    // #define KEY_numble  10
    //u_short Key[KEY_numble][5];

    //随机生成秘钥
    KeyGen(R, Keyset_num, Key);
    //建立两张，张20*out的表，一张是IN=00f0的一张是IN=0020的，把20组密钥的结果加在一起,
    int table_00f0[65536] = {}; //不能用u_short數組，会溢出！会溢出！会溢出！会溢出！
    int table_0020[65536] = {};

    clock_t start = clock();
    int inxor_0020_num = 0;
    int inxor_00f0_num = 0;
    for (int i = 0; i < Keyset_num; i++)
    {
        for (int x = 0; x < 65536; x++)
        {
            u_short tmp = CF(x, R, Key[i]);
            table_0020[tmp ^ CF(x ^ 0x0020, R, Key[i])] += 1;
            table_00f0[tmp ^ CF(x ^ 0x00f0, R, Key[i])] += 1;
        }
        // double rate = table_0020[0x0020]/(65536.0*(i+1));
        // printf("%d组随机秘钥，4轮CF，输入异或:0020，输出异或：0020，总数：%d，概率：%f\n",i+1,table_0020[0x0020],rate);
    }
    //  写入文件，有机会可以用python读文件，画一个分布图
    // ofstream fp1("task2_00f0.txt");
    // ofstream fp2("task2_0020.txt");
    // if(fp1.is_open()&&fp2.is_open())
    // {
    //     for(int i=0;i< 65536;i++)
    //         fp1<<table_00f0[i]<<endl;
    //     for(int i=0;i< 65536;i++)
    //         fp2<<table_0020[i]<<endl;
    // }

    int maxout_00f0 = max_element(table_00f0, table_00f0 + 65536) - table_00f0; //返回的是最大值所在的地址，减去起始地址，就是坐标
    double rate = table_00f0[0x00f0] / (65536.0 * Keyset_num);
    printf("%d组随机秘钥，4轮CF，输入差分:00f0，最大输出差分：%-*x，总数：%d，概率：%f\n", 
            Keyset_num, 4, maxout_00f0, table_00f0[maxout_00f0],rate);
    
    int maxout_0020 = max_element(table_0020, table_0020 + 65536) - table_0020;
    rate = table_0020[0x0020]/(65536.0 * Keyset_num);
    printf("%d组随机秘钥，4轮CF，输入差分:0020，最大输出差分：%-*x，总数：%d，概率：%f\n",
             Keyset_num, 4, maxout_0020, table_0020[maxout_0020],rate);
    //根据任务三的要求，需要找到 0x0020 ——> 0x0020的概率
    
    // double rate = table_0020[0x0020] / (65536.0 * Keyset_num);
    // //double rate = table_0020[0x0020]/inxor_0020_num;
    // printf("%d组随机秘钥，4轮CF，输入异或:0020，输出异或：0020，总数：%d，概率：%f\n", Keyset_num, table_0020[0x0020], rate);
    printf("task2共花费%fs\n", ((double)clock() - (double)start) / CLOCKS_PER_SEC);
}

void task3()
{
    printf("\n————————————————task3————————————————\n");
    int R = 4;
    //计算S盒的差分分析表
    for (int i = 0; i < 16; i++)
    { //16=0xf+1
        for (int j = 0; j < 16; j++)
        {
            u_short inxor = i ^ j;
            u_short outxor = S(i) ^ S(j);
            S_table[inxor][outxor] += 1;
        }
    }
    //打印差分分布表
    for (int i = 0; i < 16; i++)
    {
        if (!i)
        {
            printf("   ");
            for (int j = 0; j < 16; j++)
                printf("%-*x", 3, j);
            printf("\n");
        }
        printf("%-*x", 3, i);
        for (int j = 0; j < 16; j++)
            printf("%-*d", 3, S_table[i][j]);
        printf("\n");
    }
}


//随机生成2^16对16比特随机数，得到他们的差分关系
void task4()
{
    clock_t start = clock();
    printf("\n————————————————task4————————————————\n");
    u_short randxor_table[65536] = {};
    for (int i = 0; i < 65536; i++)
    {
        randxor_table[rand() & 0xffff ^ rand() & 0xffff] += 1;
    }
    printf("65536对随机数，异或为0x0020，概率：%f\n", randxor_table[0x0020] / 65536.0);
    ofstream out("task4.txt");
    if (out.is_open())
    {
        out.clear();
        for (int i = 0; i < 65536; i++)
            out << randxor_table[i] << endl;
        out.close();
    }
    printf("task4共花费%fs\n", ((double)clock() - (double)start) / CLOCKS_PER_SEC);
}

int main()
{
    srand((unsigned)time(NULL));
    u_short m = 0x00f0;
    auto R = 4;
    task3();
    task2();
    task4();
    return 0;
}