parameter i. set a to open(i):readall():binary. set b to 5. set c to lex(). for f in range(256){c:add(f,char(f)).}for g in range(a[2]){set d to "". for m in range(a[b+1]){set d to d+c[a[b+2+m]].}set c[a[b]]to d. set b to b+a[b+1]+2.}set e to "". for g in range(a[3]+a[4]*256){set e to e+c[a[b+g]].}set x to create("99:/t"+floor(random()*1e5)+".ks"). x:write(e). runpath(x).