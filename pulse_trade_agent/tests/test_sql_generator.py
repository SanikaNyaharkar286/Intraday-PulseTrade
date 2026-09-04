from agent.sql_generator import SQLGenerator


generator = SQLGenerator()



test_cases = [

    {

        "intent":"STOCK_SCREEN",

        "view":"ai_vw_scanner",

        "filters":[
            {
                "column":"rsi_oversold",
                "operator":"=",
                "value":True
            }
        ]

    },


    {

        "intent":"TOP_GAINERS",

        "view":"ai_vw_top_gainers",

        "filters":[]

    }

]



for case in test_cases:

    sql = generator.generate(case)


    print("\nGenerated SQL:")
    print(sql)