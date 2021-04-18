r = (",1,2,3,4,5,6,". split(",").index("4"))
print(r)
l = ",1,2,3,4,5,6,".split(",")
l[r] = ""
print(",".join(l))
