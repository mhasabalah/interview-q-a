we will update end point of E:\momo\MicrotecHR\Microtec.Hr.Personnel.Application\SalaryTemplates\Queries\GetById\ 

where need to add GetByIdSalaryTemplateItemDtot

SalaryItemNameEn
SalaryItemNameAr
SalaryItemCode
SalaryItemType 
SalaryItemTypeAr
SalaryItemTypeEn 
handle it please 



tab 
1 - dropdown reqired lookup 1011 came fro example with    {
        "id": "68109c74-cf0c-4d38-7c28-08de75417154",
        "name": "نموذج رقم 1",
        "paymentFrequency": "1"
    },

where is paymentFrequency is 2010 is lookup came with [{"id":"1","name":"شهري"},{"id":"2","name":"سنوي"}] fill with col 2 
2- came from paymentFrequency and map it with endpiont of  lookup 2010 and it will be disapled 
3 - 2008 the payment methoud dropdown and required 
4 - Salary terms it depend on the col 1 dropdown reqired lookup 1011 where send endpoint in choose item in dropdown of 1011 with 
https://gateway.microtecstage.com/hr-apis/api/v1/SalaryTemplates/GetAllItemsByTepmlateId?SalaryTemplateId=68109c74-cf0c-4d38-7c28-08de75417154
came with response 
[
    {
        "id": "dca1a6e1-a2de-4510-0cff-08de75417163",
        "name": "basic salary",
        "isCalculated": false
    },
    {
        "id": "d6304e61-84d9-40a7-0d00-08de75417163",
        "name": "housing allowances",
        "isCalculated": true
    },
    {
        "id": "bce400aa-52f9-4fd2-0d01-08de75417163",
        "name": "transportation allowances",
        "isCalculated": true
    },
    {
        "id": "dcf8b181-c6ff-4b47-0d02-08de75417163",
        "name": "phone allowances",
        "isCalculated": false
    }
]

and another one wit
2010