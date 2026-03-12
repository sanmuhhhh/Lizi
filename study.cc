// ============================================
// 练习题
// 求每段代码的时间复杂度 T(n) = ?
// ============================================

// ---------- Q1 ----------
#include <cstdlib>
#include <iterator>
void q1(int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += i;
    }
}
// T(n) = ? $\sum{n=0}_n-1 1$ = n = O(n)


// ---------- Q2 ----------
void q2(int n) {
    int count = 0;
    for (int i = 0; i < n; i++) {
        for (int j = i; j < n; j++) {
            count++;
        }
    }
}
// T(n) = ?
// $\sum{i=0}_n-1 \sum{j=i}_n-1 1 $ = (n+1)n/2 = O(n^2)

// ---------- Q3 ----------
void q3(int n) {
    int i = 1;
    while (i <= n) {
        i = i * 2;
    }
}
// T(n) = ?
// 令 i = 2^k, k = log2(i)
// = $\sum{k=0}_log2(n) 1 $ = log2(n) = O(logn)


// ---------- Q4 ----------
void q4(int n) {
    for (int i = 0; i < n; i++) {
        int j = 1;
        while (j < n) {
            j = j * 2;
        }
    }
}
// T(n) = ?
//令 k = log2(j) k (0,log2(n-1))
// $\sum{i=0}_n-1 sum{k=0}_log2(n-1) 1 $ = nlog2(n-1) = O(nlogn)

// ---------- Q5 ----------
void q5(int n) {
    int count = 0;
    for (int i = 1; i <= n; i = i * 3) {
        for (int j = 0; j < n; j++) {
            count++;
        }
    }
}
// T(n) = ?
//令 k = log3(i) k (0,log3(n))
// $\sum{k=0}_log3(n) sum{j=0}_n-1 1 $ = log3(n)n = O(nlogn)


// ---------- Q6 ----------
void q6(int n) {
    int x = 0;
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= i * i; j++) {
            x++;
        }
    }
}
// T(n) = ?
// $\sum{i=1}_n sum{j=1}_i^2 1 = n^3/3 = O(n^3)

// ---------- Q7 ----------
int q7(int n) {
    if (n <= 0) return 0;
    return q7(n - 1) + 1;
}
// T(n) = ?
// T(n) = T(n-1)+1 = T(n-2)+2 = T(1)+n-1 = T(0) + n = n =O(n)

// ---------- Q8 ----------
int q8(int n) {
    if (n <= 1) return 1;
    return q8(n / 2) + q8(n / 2);
}
// T(n) = ?
// T(n) = 2T(n/2) = 2^log2(n)T(1) = n * 1 = n =O(n)


// ---------- Q9 ----------
int q9(int n) {
    if (n <= 1) return 1;
    return q9(n - 1) + q9(n - 1) + q9(n - 1);
}
// T(n) = ?
// T(n) = 3T(n-1) = 3^2T(n-2) = 3^n-1T(1) = 3^n-1 = O(3^n)


// ---------- Q10 ----------
void q10(int n) {
    for (int i = 1; i < n; i = i * 2) {
        for (int j = 0; j < i; j++) {
            // do something O(1)
        }
    }
}
// T(n) = ?
// make k = log2(i) k range (0,log2(n)-1)  ; i=2^k
// $\sum{k=0}_log2(n)-1 sum{j=0}_2^k 1 = 2^k|(0,log2(n)-1) / ln2 = n/2-1 /ln2 = O(n)

void q11(int n){
    int x = 0;
    while(n>=(x+1)*(x+1))
    x = x + 1;
}
//T(n)=?
//n>=(x+1)^2  ->  n^(1/2) -1 >= x
//$\sum{x=0}_n^(1/2) - 1 = n^(1/2) -1 = O(n^(1/2))

void q12(int n){
    int count = 0;
    for(int k=1;k<=n;k=2*k){
        for(int j=1;j<=n;j++){
            count++;
        }
    }
}
//make m = log2(k) m(0,log2(k))
//$\sum{m=0}_log2(n) sum{j=1}_n 1 = log2(n)n = O(nlogn) 


// ============================================
// 线性表 - 顺序存储验证
// ============================================
#include <stdio.h>


// ============================================
// 线性表 - 单链表 
// ============================================
#include <stdlib.h> // malloc, free

#define OK 1
#define ERROR 0
typedef int Status;
typedef int ElemType;
//
typedef struct LNode {
    ElemType data;   
    struct LNode *next; 
} LNode, *LinkList;

Status InitList_L(LinkList &L) {
    // TODO: malloc a head node, set next to NULL
    L = (LinkList)malloc(sizeof(LNode));
    L->next = NULL;
    return OK;
}
Status HeadInsert_L(LinkList &L , ElemType e){
    LNode *s = (LNode*)malloc(sizeof(LNode));
    s->data = e;
    s->next = L->next;
    L->next = s;
    return OK;
}

Status EndInsert_L(LinkList &L , ElemType e){
    LNode *s = (LNode*)malloc(sizeof(LNode));
    LNode *r = L;
    while(r->next!=NULL){
        r = r->next;
    }
    s->data = e;
    s->next = NULL;
    r->next = s;
    return OK;
}

Status Query_List_Index(LinkList &L,int i,ElemType &e){
    int j=1;
    LNode *s = L->next;
    while(s && j < i){
    s = s->next;
    j++;
    }
    if(s!=NULL){
        e = s->data;
        return OK;
    }
    else{
        return ERROR;
    }
}
LNode* LocateElem_L(LinkList &L, ElemType e) {
    LNode *p = L->next;
    while (p && p->data != e) {
        p = p->next;
    }
    return p;
}

Status ListInsert_L(LinkList &L,int i,ElemType e){
    LNode* r = (LNode*)malloc(sizeof(LNode));
    r->data = e;
    LNode* s = L->next;
    int j = 1;
    while(s && j < i - 1){
        s = s->next;
        j++;
    }
    if(!s){
        return ERROR;
    }
    r->next = s->next;
    s->next = r;
    return OK;
}
Status ListDelete_L(LinkList &L, int i, ElemType &e) {
    LNode *p = L;
    int j = 0;
    while (p->next && j < i - 1) {
        p = p->next;
        j++;
    }
    if (!p->next) return ERROR;
    LNode *q = p->next;
    p->next = q->next;
    e = q->data;
    free(q);
    return OK;
}

// ============================================
// 线性表 - 单循环链表
// ============================================
typedef struct CLNode {
    ElemType data;
    struct CLNode *next;
} CLNode, *CircularList;

Status InitList_CL(CircularList &L) {
    L = (CircularList)malloc(sizeof(CLNode));
    if (!L) return ERROR;
    L->next = L;
    return OK;
}

Status TailInsert_CL(CircularList &L, ElemType e) {
    if (!L) return ERROR;
    CLNode *tail = L;
    while (tail->next != L) {
        tail = tail->next;
    }
    CLNode *s = (CLNode *)malloc(sizeof(CLNode));
    if (!s) return ERROR;
    s->data = e;
    s->next = L;
    tail->next = s;
    return OK;
}

Status ListInsert_CL(CircularList &L, int i, ElemType e) {
    if (!L || i < 0) return ERROR;
    CLNode *p = L;
    int j = 0;
    while (p->next != L && j < i) {
        p = p->next;
        j++;
    }
    if (j < i) return ERROR;
    CLNode *s = (CLNode *)malloc(sizeof(CLNode));
    if (!s) return ERROR;
    s->data = e;
    s->next = p->next;
    p->next = s;
    return OK;
}

Status ListDelete_CL(CircularList &L, int i, ElemType &e) {
    if (!L || i < 1) return ERROR;
    CLNode *p = L;
    int j = 0;
    while (p->next != L && j < i - 1) {
        p = p->next;
        j++;
    }
    if (p->next == L) return ERROR;
    CLNode *q = p->next;
    p->next = q->next;
    e = q->data;
    free(q);
    return OK;
}

void Print_CircularList(CircularList L) {
    if (!L) return;
    CLNode *p = L->next;
    while (p != L) {
        printf("%d ", p->data);
        p = p->next;
    }
    printf("\n");
}

void CircularList_demo() {
    CircularList L;
    InitList_CL(L);
    for (int i = 1; i <= 4; ++i) {
        TailInsert_CL(L, i * 10);
    }
    Print_CircularList(L);
    ElemType e;
    ListInsert_CL(L, 2, 25);
    Print_CircularList(L);
    ListDelete_CL(L, 1, e);
    Print_CircularList(L);
}

// ============================================
// 线性表 - 双向循环链表
// ============================================
typedef struct DNode {
    ElemType data;
    struct DNode *prior;
    struct DNode *next;
} DNode, *DLinkList;

Status InitList_D(DLinkList &L) {
    L = (DLinkList)malloc(sizeof(DNode));
    if (!L) return ERROR;
    L->prior = L;
    L->next = L;
    return OK;
}

Status ListInsert_D(DLinkList &L, int i, ElemType e) {
    if (!L || i < 0) return ERROR;
    DNode *p = L;
    int j = 0;
    while (p->next != L && j < i) {
        p = p->next;
        j++;
    }
    if (j < i) return ERROR;
    DNode *s = (DNode *)malloc(sizeof(DNode));
    if (!s) return ERROR;
    s->data = e;
    s->next = p->next;
    s->prior = p;
    p->next->prior = s;
    p->next = s;
    return OK;
}

Status ListDelete_D(DLinkList &L, int i, ElemType &e) {
    if (!L || i < 1) return ERROR;
    DNode *p = L->next;
    int j = 1;
    while (p != L && j < i) {
        p = p->next;
        j++;
    }
    if (p == L) return ERROR;
    e = p->data;
    p->prior->next = p->next;
    p->next->prior = p->prior;
    free(p);
    return OK;
}

void Print_DList_Forward(DLinkList L) {
    if (!L) return;
    DNode *p = L->next;
    while (p != L) {
        printf("%d ", p->data);
        p = p->next;
    }
    printf("\n");
}

void Print_DList_Backward(DLinkList L) {
    if (!L) return;
    DNode *p = L->prior;
    while (p != L) {
        printf("%d ", p->data);
        p = p->prior;
    }
    printf("\n");
}

void DList_demo() {
    DLinkList L;
    InitList_D(L);
    for (int i = 1; i <= 3; ++i) {
        ListInsert_D(L, i - 1, i * 5);
    }
    Print_DList_Forward(L);
    Print_DList_Backward(L);
    ElemType e;
    ListDelete_D(L, 2, e);
    Print_DList_Forward(L);
}

// 2019 408 Q41: Given L = (a1, a2, ..., an-1, an), reorder to (a1, an, a2, an-1, ...)
Status ReorderList_2019(LinkList &L) {
    if (!L || !L->next || !L->next->next) return OK;
    LNode *slow = L->next;
    LNode *fast = L->next;
    while (fast->next && fast->next->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    LNode *second = slow->next;
    slow->next = NULL;
    LNode *prev = NULL;
    while (second) {
        LNode *next = second->next;
        second->next = prev;
        prev = second;
        second = next;
    }
    second = prev;
    LNode *first = L->next;
    while (second) {
        LNode *nextFirst = first ? first->next : NULL;
        LNode *nextSecond = second->next;
        first->next = second;
        second->next = nextFirst;
        first = nextFirst ? nextFirst : second;
        second = nextSecond;
    }
    return OK;
}

void Practice_2019_Q41() {
    LinkList L;
    InitList_L(L);
    int data[] = {1, 2, 3, 4, 5, 6};
    for (int i = 0; i < 6; ++i) {
        EndInsert_L(L, data[i]);
    }
    printf("Before reorder: ");
    LNode *p = L->next;
    while (p) {
        printf("%d ", p->data);
        p = p->next;
    }
    printf("\n");
    ReorderList_2019(L);
    printf("After reorder (2019 Q41 pattern): ");
    p = L->next;
    while (p) {
        printf("%d ", p->data);
        p = p->next;
    }
    printf("\n");
}

// 2016 408 Q2: Delete node p from a doubly circular list with prev/next pointers
Status DeleteNode_2016(DLinkList &L, DNode *p) {
    if (!L || !p || p == L) return ERROR;
    p->prior->next = p->next;
    p->next->prior = p->prior;
    free(p);
    return OK;
}

void Practice_2016_Q2() {
    DLinkList L;
    InitList_D(L);
    for (int i = 0; i < 5; ++i) {
        ListInsert_D(L, i, (i + 1) * 10);
    }
    printf("Before delete (doubly circular): ");
    Print_DList_Forward(L);
    DNode *p = L->next->next; // use third data node as sample target
    DeleteNode_2016(L, p);
    printf("After delete (2016 Q2 pointer rule): ");
    Print_DList_Forward(L);
}
void List_print(){
    LinkList L;
    printf("%s",InitList_L(L)?"成功":"失败");
}
void seq_list_demo() {
    int arr[10] = {1,2,3,4,5};
    int *a = arr;
    for(int i=0;i<4;i++){
        a[i] = 9;
        printf("addr:%p\n",(void*)&a[i]);
    }
    int x = 99;
    for(int j = 4;j>0;--j){
        a[j+1]=a[j];
    }
    a[1] = x;
    for(int i=0;i<9;++i){
        printf("a[%d]:%d\n",i,a[i]);
    }
}

void List_print_Insert(){
    LinkList L;
    InitList_L(L);
    for(int i=0;i<3;++i){
    EndInsert_L(L, i);
    }
    LNode *p = L->next;
    while(p!=NULL){
        printf("节点值:%d",p->data);
        p = p->next;
    }  
}
int main() {
    //seq_list_demo();
    //List_print();
    List_print_Insert();
    CircularList_demo();
    DList_demo();
    Practice_2019_Q41();
    Practice_2016_Q2();
    return 0;
}

// ============================================
// Exercises
// ============================================

// [Q1] 2021 408
// h points to a non-empty circular linked list with a head node.
// p is the tail pointer, q is a temp pointer.
// To delete the first element, which is correct?
//
// A. h->next = h->next->next; g = h->next; free(g);
// B. g = h->next; h->next = h->next->next; free(g);
// C. g = h->next; h->next = g->next; if (p != g) p = h; free(g);
// D. g = h->next; h->next = g->next; if (p == g) p = h; free(g);
//
// Answer: 
/*
h->next (this is we want to delete)
so A is error ,because g is caucalated answer ,B ,C ,D first is g = h->next (true)
i think B is true ,but i see C and D later,I think B is 缺少 correct p
so answer is D

*/

// [Q2] 2016 408
// A doubly circular linked list L with a head node.
// Node structure: prev | data | next
// prev and next point to the predecessor and successor respectively.
// To delete the node pointed by p, which is correct?
//
// A. p->next->prev = p->prev; p->prev->next = p->prev; free(p);
// B. p->next->prev = p->next; p->prev->next = p->next; free(p);
// C. p->next->prev = p->next; p->prev->next = p->prev; free(p);
// D. p->next->prev = p->prev; p->prev->next = p->next; free(p);
//
// Answer: 
/*
all need to free(p),this is true
then obsolutely B and C is error ,A p->prev->next = p->prev is false 
so answer is D
*/

// [Q41] 2019 408
// Singly linked list L = (a1, a2, ..., an-1, an) has a head node.
// Rearrange nodes in-place so the order becomes (a1, an, a2, an-1, a3, an-2, ...).
// Requirements: time O(n), extra space O(1).
//
// Answer idea:
// 1. Find middle via slow/fast pointers.
// 2. Reverse the second half in place.
// 3. Alternate merge the first half and reversed half.
/*



*/

// [Q2] 2016 408
// A doubly circular linked list L with a head node.
// Node structure: prev | data | next. prev/next point to predecessor/successor.
// To delete node p, which statement sequence is correct?
//
// A. p->next->prev = p->prev; p->prev->next = p->prev; free(p);
// B. p->next->prev = p->next; p->prev->next = p->next; free(p);
// C. p->next->prev = p->next; p->prev->next = p->prev; free(p);
// D. p->next->prev = p->prev; p->prev->next = p->next; free(p);
//
// Answer: D (others break links; final step free(p)).
/*
this is easy , for delete node p ,             p->prev->next need p->next 
p->next->prev need p->prev so answer is D

*/

// [Q7] 2009 408
// A singly linked list with head node is given (only head pointer 'list' provided).
// Design an algorithm to find the k-th node from the END of the list (k >= 1).
// If found, output the node's data and return 1; otherwise return 0.
// Requirements: as efficient as possible in time.
//
// Answer:
int FindKthFromEnd(LinkList list, int k) {
    LNode *p = list->next, *q = list->next;
    // step 1: p 先走 k 步
    for (int i = 0; i < k; i++) {
        if (!p) return 0;  // 链表长度不足 k
        p = p->next;
    }
    // step 2: p、q 同步走，直到 p 为 NULL
    while (p) {
        p = p->next;
        q = q->next;
    }
    // 此时 q 就是倒数第 k 个节点
    printf("%d\n", q->data);
    return 1;
}

// [Q8] 2012 408
// Two words are stored as singly linked lists (one char per node) with head nodes.
// When two words share a common suffix, they share the same tail nodes in memory.
// e.g. "loading" and "being" share suffix "ing".
// Given head pointers str1 and str2, design a time-efficient algorithm to find
// the starting node of their common suffix.
//
// Answer:
// 1. 分别求两链表长度 len1、len2
// 2. 长的先走 |len1-len2| 步，对齐尾部
// 3. 同步走，第一个地址相同的节点就是公共后缀起点
LNode* FindCommonSuffix(LinkList str1, LinkList str2) {
    // 求长度
    int len1 = 0, len2 = 0;
    LNode *p = str1->next, *q = str2->next;
    while (p) { len1++; p = p->next; }
    while (q) { len2++; q = q->next; }

    // 重置，长的先走
    p = str1->next;
    q = str2->next;
    if (len1 > len2)
        for (int i = 0; i < len1 - len2; i++) p = p->next;
    else
        for (int i = 0; i < len2 - len1; i++) q = q->next;

    // 同步走找交点（比较地址，不是值）
    while (p && q && p != q) {
        p = p->next;
        q = q->next;
    }
    return p;  // NULL 表示无公共后缀
}

// [Q9] Custom
// A non-empty singly linked list with head node has an UNKNOWN length.
// The following operations are performed:
//   (1) pointer p starts at head->next, moves 1 step each time
//   (2) pointer q starts at head->next, moves 2 steps each time
//   (3) when q reaches NULL or q->next reaches NULL, p stops
// Which of the following statements is CORRECT?
//
// A. p always points to the last node of the list
// B. p always points to the middle node (ceil(n/2)-th) of the list
// C. if the list has a cycle, p and q will never meet
// D. this technique can be used to detect whether the list has a cycle
//
// Answer:
/*
B. p always points to the middle node (ceil(n/2)-th)
- q 走 2 步，p 走 1 步，q 到头时 p 正好在中间
- A 错：p 在中间不在末尾
- C 错：有环时 q 会追上 p，两者会相遇
- D 错：此代码遇到环会死循环，无法检测
*/

// [Q10] Custom
// Given a circular singly linked list with head node (tail->next == head),
// n data nodes, and a pointer 'tail' that always points to the last node.
// To insert a new node s AFTER the head node, which sequence is correct?
//
// A. s->next = head->next; head->next = s;
// B. head->next = s; s->next = head->next;
// C. s->next = head->next; head->next = s; if (tail == head) tail = s;
// D. s->next = head->next; head->next = s; if (tail->next != head) tail = s;
//
// Answer:
/*
    s after head ,so s->next = head->next is correct ,ab errot answer is C
*/

// [Q11] Custom (Networking)
// For a real-time pub/sub system (e.g., DDS-Data Distribution Service) choosing UDP vs TCP, which statement is CORRECT?
// A. TCP always gives lower latency because of reliability and ordering
// B. UDP with app-level reliability/ordering avoids TCP head-of-line blocking and supports multicast fan-out
// C. Multicast discovery requires TCP, so UDP cannot be used
// D. UDP cannot recover loss even if the app adds reliability/ordering
//
// Answer:B

// [Q12] Custom (Networking)
// For a TCP connection, which combination is valid during slow start and congestion avoidance?
// A. cwnd doubles each RTT in both phases
// B. cwnd doubles in slow start; grows linearly (additive increase) in congestion avoidance
// C. cwnd grows linearly in slow start; doubles in congestion avoidance
// D. cwnd stays constant until ssthresh is reached
//
// Answer:B
