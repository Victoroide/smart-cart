REPORT_TYPES = {
    'SALES_BY_CUSTOMER': 'sales_by_customer',
    'BEST_SELLERS': 'best_sellers',
    'SALES_BY_PERIOD': 'sales_by_period',
    'PRODUCT_PERFORMANCE': 'product_performance',
    'INVENTORY_STATUS': 'inventory_status',
    'ORDER_RECEIPT': 'order_receipt',
    'CUSTOMER_ORDERS': 'customer_orders',
}

REPORT_FORMATS = {
    'JSON': 'json',
    'PDF': 'pdf',
    'EXCEL': 'excel',
}

USER_REPORT_PERMISSIONS = {
    'admin': [
        REPORT_TYPES['SALES_BY_CUSTOMER'],
        REPORT_TYPES['BEST_SELLERS'],
        REPORT_TYPES['SALES_BY_PERIOD'],
        REPORT_TYPES['PRODUCT_PERFORMANCE'],
        REPORT_TYPES['INVENTORY_STATUS'],
        REPORT_TYPES['ORDER_RECEIPT'],
    ],
    'customer': [
        REPORT_TYPES['ORDER_RECEIPT'],
        REPORT_TYPES['CUSTOMER_ORDERS'],
    ]
}