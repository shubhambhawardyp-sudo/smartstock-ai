-- Optional sales demonstration seed; run after schema.sql. Dates are recent relative to execution.
INSERT INTO sales(invoice_number,sold_at,total_amount) VALUES ('DEMO-0001',DATE_SUB(NOW(),INTERVAL 1 DAY),15.98),('DEMO-0002',DATE_SUB(NOW(),INTERVAL 2 DAY),9.98),('DEMO-0003',DATE_SUB(NOW(),INTERVAL 3 DAY),7.99);
INSERT INTO sale_items(sale_id,product_id,quantity,unit_price,line_total) VALUES (1,1,2,7.99,15.98),(2,5,2,4.99,9.98),(3,1,1,7.99,7.99);
INSERT INTO stock_movements(product_id,movement_type,quantity,reason,reference) VALUES (1,'SALE',-2,'Seed demonstration sale','DEMO-0001'),(5,'SALE',-2,'Seed demonstration sale','DEMO-0002'),(1,'SALE',-1,'Seed demonstration sale','DEMO-0003');
UPDATE products SET stock_quantity=stock_quantity-3 WHERE id=1;
UPDATE products SET stock_quantity=stock_quantity-2 WHERE id=5;
