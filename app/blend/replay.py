from collections import defaultdict

from app.blend.share import split_mass


def rebuild(records):
    balances=defaultdict(lambda:defaultdict(int))
    provenance=defaultdict(lambda:defaultdict(list))
    evidence,isolated=[],[]
    for row in records:
        fields=row['data']
        pot,action=fields['pot'],fields['action']
        stock=balances[pot]
        before=dict(stock)
        prior={lot:list(lines) for lot,lines in provenance[pot].items()}
        net=row['net_mg']
        if action in {'OPEN','ISSUE'}:
            parts={row['lot']:net}
            stock[row['lot']]+=net
            provenance[pot][row['lot']].append(row['line'])
        else:
            try:
                parts=split_mass(net,stock)
            except ValueError as error:
                isolated.append(row | {'code':str(error),'before_mg':before})
                continue
            for lot, amount in parts.items():
                stock[lot]-=amount
                if stock[lot]==0:
                    provenance[pot][lot].clear()
        lines={lot: list(provenance[pot][lot]) for lot in parts}
        if action not in {'OPEN','ISSUE'}:
            # 从清空前的取料记录追踪本次归属。
            lines={lot:prior[lot] for lot in parts}
        evidence.append(row | {'before_mg':before,'parts_mg':parts,'after_mg':dict(stock),'issue_lines':lines})
    pending={pot:{lot:mass for lot,mass in stock.items() if mass} for pot,stock in balances.items()}
    return {'rows':evidence,'isolated':isolated,'pending_mg':pending}
