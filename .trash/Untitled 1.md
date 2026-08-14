
we need add tab name Compensation and payroll info
1 - (Salary Model) dropdown reqired lookup 1011 came fro example with    {
        "id": "68109c74-cf0c-4d38-7c28-08de75417154",
        "name": "نموذج رقم 1",
        "paymentFrequency": "1"
    },

after user choose from downdown for example "id": "68109c74-cf0c-4d38-7c28-08de75417154"
so we will make endpoint by id with name SalaryTemplates/GetById?Id=68109c74-cf0c-4d38-7c28-08de75417154

came with result we just handled in GetByIdSalaryTemplateQueryResponse 


2-Payment Frequency came from PaymentFrequencyName in  GetByIdSalaryTemplateQueryResponse and make it read only 
3 - Payment method dropdown with  2008 the payment methoud dropdown and required 
4 - Salary terms it depend on  GetByIdSalaryTemplateQueryResponse where shoud get dropdown from Salary item that it is list of GetByIdSalaryTemplateQueryResponse where have 
    public string? SalaryItemNameAr { get; set; }
    public string? SalaryItemNameEn { get; set; }
    public Guid SalaryItemId { get; set; }
    public string? SalaryItemType { get; set; }
    public string? SalaryItemTypeAr { get; set; }
    public string? SalaryItemTypeEn { get; set; }
    bool is calcualted or not
    
    where it will be table with add inline like in 
    
    1st col dropdown with list of salery items 
     2th col is result of choose the dropdown where apear SalaryItemTypeAr or SalaryItemTypeEn based on lang and it will not editable 
     3th row Salary item value this is triky where it will depend on the isCalculated bool where is false user can set the Salary item value   
    if true 
    calc endpoint and make E:\momo\MicrotecHR\Microtec.Hr.Personnel.Application\SalaryTemplates\Commands\Calc\CalcSalaryTemplateItemCommandHandler.cs
    
    where will wait take result from endpoint and make fild disabled 
    make validation and logical one take table desgin form vacation tab in same page 
    
    
5- total salery the calc of all salery terms and it readonly 