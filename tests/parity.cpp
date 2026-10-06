#include "PixelLogic.h"
#include <iostream>
int main() {
 pixeltool::Model m;m.count=50;m.used=2;m.ends[0]=10;m.ends[1]=30;
 for(int mode=0;mode<=12;++mode)for(int tick: {0,300,600,1200,5000})for(int n=1;n<=50;++n){
 int step=(tick/100)%12;
 int pulse=12*(45+55*(step<6?step%6:11-step)/5)/100;
 auto c=pixeltool::colour(n-1,mode,15,10,20,10,3,5,m,12,pulse,tick);
 std::cout<<int(c.r)<<","<<int(c.g)<<","<<int(c.b)<<"\n";
 }
}
