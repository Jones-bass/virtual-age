## Request

```bash
{
  "filter": {
    "change": {
      "startDate": "2025-11-03T23:21:06.439Z",
      "endDate": "2025-11-03T23:21:06.439Z"
    },
    "startOrderDate": "2025-11-03T23:21:06.439Z",
    "endOrderDate": "2025-11-03T23:21:06.439Z",
    "branchCodeList": [
      0
    ],
    "orderCodeList": [
      0
    ],
    "orderIdList": [
      "string"
    ],
    "customerOrderCodeList": [
      "string"
    ],
    "integrationCodeList": [
      "string"
    ],
    "customerCodeList": [
      0
    ],
    "customerCpfCnpjList": [
      "string"
    ],
    "representativeCodeList": [
      0
    ],
    "representativeCpfCnpjList": [
      "string"
    ],
    "orderStatusList": [
      "InProgress"
    ],
    "operationCodeList": [
      0
    ],
    "startBillingForecastDate": "2025-11-03T23:21:06.439Z",
    "endBillingForecastDate": "2025-11-03T23:21:06.439Z",
    "hasShippingCompany": true,
    "hasPdvTransaction": true,
    "hasFinancialProcessed": true,
    "classifications": [
      {
        "type": 0,
        "codeList": [
          "string"
        ]
      }
    ],
    "experienceTypeList": [
      "Ecommerce"
    ]
  },
  "expand": "string",
  "order": "string",
  "page": 0,
  "pageSize": 0
}

## Response
```bash
{
  "count": 0,
  "totalPages": 0,
  "hasNext": true,
  "totalItems": 0,
  "items": [
    {
      "branchCode": 0,
      "orderCode": 0,
      "orderId": "string",
      "customerOrderCode": "string",
      "insertDate": "2025-11-03T23:21:06.442Z",
      "integrationCode": "string",
      "guideCode": 0,
      "guideCpfCnpj": "string",
      "sellerCode": 0,
      "sellerCpfCnpj": "string",
      "orderDate": "2025-11-03T23:21:06.442Z",
      "maxChangeFilterDate": "2025-11-03T23:21:06.442Z",
      "arrivalDate": "2025-11-03T23:21:06.442Z",
      "customerCode": 0,
      "customerCpfCnpj": "string",
      "customerName": "string",
      "representativeCode": 0,
      "representativeCpfCnpj": "string",
      "representativeName": "string",
      "operationCode": 0,
      "operationName": "string",
      "paymentConditionCode": 0,
      "paymentConditionName": "string",
      "quantity": 0,
      "grossValue": 0,
      "discountValue": 0,
      "netValue": 0,
      "freightType": "CIF",
      "freightValue": 0,
      "shippingCompanyCode": 0,
      "shippingCompanyCpfCnpj": "string",
      "shippingCompanyName": "string",
      "redispatchingFreightType": "CIF",
      "redispatchingShippingCompanyCode": 0,
      "redispatchingShippingCompanyCpfCnpj": "string",
      "redispatchingShippingCompanyName": "string",
      "totalAmountOrder": 0,
      "statusOrder": "InProgress",
      "reasonBlockingCode": 0,
      "reasonBlockingDescription": "string",
      "reasonCancellationCode": 0,
      "reasonCancellationDescription": "string",
      "omniSiteId": 0,
      "experienceType": "Ecommerce",
      "hasPdvTransaction": true,
      "hasFinancialProcessed": true,
      "priceTableCode": 0,
      "shippingService": "string",
      "shippingServiceName": "string",
      "cancellationLimitDate": "2025-11-03T23:21:06.442Z",
      "billingForecastDate": "2025-11-03T23:21:06.442Z",
      "billingLimitDate": "2025-11-03T23:21:06.442Z",
      "lastBillingDate": "2025-11-03T23:21:06.442Z",
      "paymentBaseDate": "2025-11-03T23:21:06.442Z",
      "batchOrder": "string",
      "rollMeasureCode": 0,
      "rollMeasureDescription": "string",
      "ecommerceStage": "string",
      "items": [
        {
          "productCode": 0,
          "name": "string",
          "referenceCode": "string",
          "referenceName": "string",
          "productSku": "string",
          "colorCode": "string",
          "colorName": "string",
          "sizeName": "string",
          "quantity": 0,
          "toSettleQuantity": 0,
          "settledQuantity": 0,
          "canceledQuantity": 0,
          "extraQuantity": 0,
          "pendingQuantity": 0,
          "originalPrice": 0,
          "price": 0,
          "discountPercentage": 0,
          "lastChangeUserInsert": 0,
          "lastChangeDate": "2025-11-03T23:21:06.442Z",
          "billingForecastDate": "2025-11-03T23:21:06.442Z",
          "insertDate": "2025-11-03T23:21:06.442Z",
          "cancellationLimitDate": "2025-11-03T23:21:06.442Z",
          "billingLimitDate": "2025-11-03T23:21:06.442Z",
          "lastBillingDate": "2025-11-03T23:21:06.442Z",
          "rollMeasureCode": 0,
          "rollMeasureDescription": "string",
          "customerOrderCode": 0,
          "customerProductCode": "string",
          "batchItems": [
            {
              "sequence": 0,
              "branchCode": 0,
              "code": 0,
              "quantity": 0
            }
          ]
        }
      ],
      "invoices": [
        {
          "accessKey": "string",
          "code": 0,
          "serial": "string",
          "issueDate": "2025-11-03T23:21:06.442Z",
          "status": "Canceled",
          "shippingCompanyName": "string",
          "packageNumber": 0,
          "grossWeight": 0,
          "netWeight": 0,
          "trackingCode": "string",
          "discountPercentage": 0,
          "quantity": 0,
          "productValue": 0,
          "additionalValue": 0,
          "shippingValue": 0,
          "InsuranceValue": 0,
          "ipiValue": 0,
          "totalValue": 0,
          "transactionBranchCode": 0,
          "transactionDate": "2025-11-03T23:21:06.442Z",
          "transactionCode": 0,
          "electronic": {
            "accessKey": "string",
            "electronicInvoiceStatus": "Authorized",
            "receipt": 0,
            "receivementDate": "2025-11-03T23:21:06.442Z"
          }
        }
      ],
      "shippingAddress": {
        "addressType": "Commercial",
        "publicPlace": "string",
        "address": "string",
        "number": 0,
        "complement": "string",
        "addressSequence": 0,
        "neighborhood": "string",
        "ibgeCityCode": 0,
        "cityName": "string",
        "stateAbbreviation": "string",
        "cep": "string",
        "bcbCountryCode": 0,
        "countryName": "string",
        "postOfficeBox": 0,
        "reference": "string"
      },
      "observations": [
        {
          "observation": "string"
        }
      ],
      "invoiceObservations": [
        {
          "observation": "string"
        }
      ],
      "representativeObservations": [
        {
          "observation": "string",
          "visualizationType": "Sugestion"
        }
      ],
      "classifications": [
        {
          "typeCode": 0,
          "typeName": "string",
          "code": "string",
          "name": "string"
        }
      ],
      "discounts": [
        {
          "typeDiscountCode": 0,
          "description": "string",
          "discountPercentage": 0,
          "discountValue": 0
        }
      ],
      "commissioneds": [
        {
          "representativeCode": 0,
          "representativeName": "string",
          "commissionPercentageBilling": 0,
          "commissionPercentageReceipt": 0,
          "commissionedType": "Representative"
        }
      ],
      "counts": [
        {
          "branchCode": 0,
          "code": 0,
          "description": "string",
          "statusCount": "InProgress",
          "packagingTypeCode": 0,
          "packagingTypeDescription": "string",
          "separator": 0,
          "separatorName": "string"
        }
      ]
    }
  ]
}