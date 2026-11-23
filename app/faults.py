class LedgerError(Exception):
    def __init__(self, code, message, status=422):
        super().__init__(message)
        self.code, self.status = code, status


REASONS = {
    'WIDTH':'列数不符', 'BLANK':'空行', 'MISSING_MASS':'重量缺失', 'BAD_MASS':'重量格式错误',
    'BAD_UNIT':'单位无效', 'BAD_TIME':'时间无偏移或收件顺序错误', 'BAD_ACTION':'动作无效',
    'BAD_KEY':'编号空缺', 'TICKET_CONFLICT':'同号秤单冲突', 'TICKET_DUPLICATE':'重复秤单',
    'OUTSIDE':'超出盘点窗口', 'AFTER_CUTOFF':'迟于封账', 'TARE_MISSING':'无生效皮重',
    'TARE_OVERLAP':'皮重版本重叠', 'TARE_RANGE':'皮重区间倒置', 'NEGATIVE_NET':'负净量',
    'LOT_UNKNOWN':'颜料别名未登记', 'LOT_CONFLICT':'别名关联多个批号', 'MIXED_OUTPUT':'混料动作不得指定单一批号',
    'OVERDRAW':'净重超过罐内存量', 'CLAIM_CONFLICT':'同批申报值冲突', 'NO_CLAIM':'无回桶申报',
    'MISMATCH':'回桶差异', 'MATCH':'账实一致', 'ACCEPTED':'已采信',
}
