# TODO
## main.py
- Finish websocket integration
- Data Persistance (pickle? nosql?)

## Klines.py
- [update_klines()] Handle case where missing klines > Klines.max_klines
- [compute_heikin_ashi()]  compute only for update instead of all the frame each time

## BinanceAPI.py
- Extend functionalities
- Fine grain handling of errors

## statistics.py
- [plot_candlestick()] Handle indicators like MACD that should have their own subplot with multiple

## Wallets.py
- Handle orders stacking
- Let the choice or handle fee_maker vs fee_taker
- [push_order()] Handle returned "fills" in case of real orders for more precise price & quantity
- [push_order()] handle potential precision issue on quantity and minimum amount