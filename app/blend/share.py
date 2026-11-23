def split_mass(net, stock):
    available=sum(stock.values())
    if net>available:
        raise ValueError('OVERDRAW')
    if available==0:
        return {}
    parts={lot:divmod(net*mass,available) for lot,mass in stock.items() if mass>0}
    allocated={lot:part for lot,(part,_) in parts.items()}
    left=net-sum(allocated.values())
    ranks=sorted(parts,key=lambda lot:(-parts[lot][1],lot))
    for lot in ranks[:left]:
        allocated[lot]+=1
    return {lot:amount for lot,amount in allocated.items() if amount}
