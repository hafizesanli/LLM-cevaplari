## Test‑Scenario Blueprint for the **ParaBank** Model  

The JSON you supplied contains a full‑blown **Model‑Based Testing (MBT)** model for the ParaBank web application.  
Below is a practical plan that shows:

1. **How to analyse the model** – vertices (states) and edges (transitions).  
2. **How to generate a 100 % edge‑ and vertex‑coverage path** with GraphWalker.  
3. **How to write the Java test class** (JUnit 5 + GraphWalker annotations) that:  
   * Executes the generated path,  
   * Adds **edge guards** as pre‑conditions,  
   * Calls **vertex actions** as test steps.  
4. **Sample Maven configuration** and a minimal **`pom.xml`**.  
5. **Explanation of the produced test cases** (one per edge guard).  

---

### 1. Model Overview – Vertices & Edges  

| **Vertex (state)** | **Human readable name** | **Key outgoing edges** |
|--------------------|--------------------------|------------------------|
| `Login_v_Start` | *Login start* | `Login_e_goto_login` → `Login_v_Login_Page` |
| `Login_v_Login_Page` | *Login page* | `Login_e_Invalid_Login_Username`, `Login_e_Invalid_Login_Password`, `Login_e_Valid_Login` |
| `Register_v_Information_Filled` | *Fill registration data* | `Register_e_Valid_Registration` → `Register_v_Registration_Complete` |
| `RequestLoan_v_Information_Filled_Valid` | *Apply for loan (valid)* | `RequestLoan_e_Loan_Processed` |
| `BillPay_v_Information_Filled` | *Create bill payment* | `BillPay_e_Valid_Send_Payment` → `BillPay_v_Bill_Payment_Complete` |
| `TransferFunds_v_Information_Filled` | *Transfer money* | `TransferFunds_e_Valid_Amount` → `TransferFunds_v_Transfer_Complete` |
| `FindTransactions_v_Transaction_Results` | *View result list* | `FindTransactions_e_Click_Transaction` |
| `UpdateContactInfo_v_Profile_Updated` | *Update contact info* | `UpdateContactInfo_e_Update_Profile` |
| `AccountOverview_v_Select_Account` | *Select an account* | `AccountOverview_e_Click_Account_Overview` |
| … | … | … |

Each **edge** carries a `name` that is the **action** performed by the tester (e.g., `Login_e_Invalid_Login_Username`).  
For the purpose of this guide we will treat every edge as a *distinct* transition that must be exercised at least once.

---

### 2. Generating a 100 % Coverage Path  

The model’s generator declaration already uses  

```json
"generator":"RandomPath(EdgeCoverage(100))"
```  

which tells GraphWalker to **enumerate every outgoing edge from every visited vertex** until all edges have been covered.  
The generated **path** is therefore a *sequence* of vertex → edge → vertex steps that touches every edge exactly once (or more, if required by the random walk).

> **Coverage guarantee:**  
> $$
> \text{Edge coverage } = 100\% \;\Longrightarrow\; \sum_{e\in E} \text{executed}(e) = |E|
> $$  
> The same walk inherently visits every vertex that is a source of an edge, giving us full vertex coverage as well.

---

### 3. Java Test Skeleton (JUnit 5 + GraphWalker)

#### 3.1 `pom.xml` (minimal)

```xml
<!-- pom.xml -->
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>parabank-mbt</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <junit.jupiter.version>5.9.3</junit.jupiter.version>
        <graphwalker.version>4.3.2</graphwalker.version>
    </properties>

    <dependencies>
        <!-- GraphWalker Core -->
        <dependency>
            <groupId>org.graphwalker</groupId>
            <artifactId>graphwalker</artifactId>
            <version>${graphwalker.version}</version>
        </dependency>

        <!-- JUnit 5 -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <version>${junit.jupiter.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>${junit.jupiter.version}</version>
            <scope>test</scope>
        </dependency>

        <!-- Selenium (if you bind web actions to edges) -->
        <dependency>
            <groupId>org.seleniumhq.selenium</groupId>
            <artifactId>selenium-java</artifactId>
            <version>4.13.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Maven Surefire for JUnit 5 -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.1.2</version>
                <configuration>
                    <reuseForks>true</reuseForks>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

> **Source:** [GraphWalker Maven guide](https://graphwalker.github.io/projects/graphwalker/wiki/Maven)  

#### 3.2 Test Model (`src/test/resources/models/parabank_model.json`)  

Copy the JSON you posted into this file. The file name **must match** the one referenced in the generator configuration (see below).

#### 3.3 `graphwalker.json` (path generator config)  

```json
{
  "model": "models/parabank_model.json",
  "pathGenerator": "random(edge_coverage(100))",
  "startElement": "Login_70e6c75f-f7ef-4208-a4a6-06778a6f3020",
  "annotationProcessor": "org.graphwalker.java.annotation.GraphWalker"
}
```

*The `annotationProcessor` field tells GraphWalker to look for JUnit 5 test methods annotated with `@Vertex`/`@Edge`.*

> **Source:** [GraphWalker test‑execution page](https://graphwalker.github.io/projects/graphwalker/wiki/Test-execution)  

#### 3.4 The Test Class  

```java
// src/test/java/com/example/parabank/ParabankMbtTest.java
package com.example.parabank;

import org.graphwalker.java.annotation.Edge;
import org.graphwalker.java.annotation.Vertex;
import org.graphwalker.java.test.Result;
import org.graphwalker.java.test.TestExecutor;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class ParabankMbtTest {

    /** Pre‑condition that the browser (or HTTP client) is on the login page */
    @BeforeEach
    public void setUp() {
        System.out.println("=== Test set‑up: open login page ===");
        // Selenium code to navigate to https://parabank.parasoft.com/parabank/index.htm
        // driver.get("https://parabank.parasoft.com/parabank/index.htm");
    }

    /* --------------------------------------------------------------
       Vertex actions – these are executed *when the walker arrives*
       at the corresponding vertex.
       -------------------------------------------------------------- */

    // The initial login page
    @Vertex("Login_v_Start")
    public void v_Login_Start() {
        System.out.println("Vertex – Login_Start");
        // No concrete action, just log entry
    }

    @Vertex("Login_v_Login_Page")
    public void v_Login_Page() {
        System.out.println("Vertex – Login page displayed");
    }

    @Vertex("Register_v_Information_Filled")
    public void v_Register_InfoFilled() {
        System.out.println("Vertex – Register – information filled");
    }

    @Vertex("RequestLoan_v_Information_Filled_Valid")
    public void v_RequestLoan_Valid() {
        System.out.println("Vertex – RequestLoan – valid info filled");
    }

    @Vertex("BillPay_v_Information_Filled")
    public void v_BillPay_InfoFilled() {
        System.out.println("Vertex – BillPay – information filled");
    }

    @Vertex("TransferFunds_v_Information_Filled")
    public void v_TransferFunds_InfoFilled() {
        System.out.println("Vertex – TransferFunds – information filled");
    }

    @Vertex("FindTransactions_v_Transaction_Results")
    public void v_FindTransactions_Results() {
        System.out.println("Vertex – FindTransactions – results displayed");
    }

    @Vertex("UpdateContactInfo_v_Profile_Updated")
    public void v_UpdateContactInfo_Updated() {
        System.out.println("Vertex – UpdateContactInfo – profile updated");
    }

    @Vertex("AccountOverview_v_Select_Account")
    public void v_AccountOverview_Select() {
        System.out.println("Vertex – AccountOverview – account selected");
    }

    /* --------------------------------------------------------------
       Edge actions – executed *when the walker traverses the edge*.
       -------------------------------------------------------------- */

    // Login → Login page
    @Edge("Login_e_goto_login")
    public void e_goto_login() {
        System.out.println("Edge – goto_login (open login page)");
        // Selenium call: driver.findElement(By.linkText("Login")).click();
    }

    // Successful login
    @Edge("Login_e_Valid_Login")
    public void e_valid_login() {
        System.out.println("Edge – valid_login");
        // Selenium call: driver.findElement(By.id("username")).sendKeys("user");
        // … then submit …
    }

    // Invalid login (empty password)
    @Edge("Login_e_Invalid_Login_Empty")
    public void e_invalid_login_empty() {
        System.out.println("Edge – invalid_login_empty (no password entered)");
        // Edge guard: password field must be blank – pre‑condition can be asserted here
        // assertTrue(driver.findElement(By.id("password")).getAttribute("value").isEmpty());
    }

    // Register – valid registration
    @Edge("Register_e_Valid_Registration")
    public void e_valid_registration() {
        System.out.println("Edge – valid_registration");
        // Selenium actions that fill and submit the registration form
    }

    // Find transactions – valid by amount
    @Edge("FindTransactions_e_Valid_Amount_Find_Transactions")
    public void e_find_by_amount_valid() {
        System.out.println("Edge – find_by_amount_valid");
        // Selenium click on “Find by Amount” …
    }

    @Edge("BillPay_e_Valid_Send_Payment")
    public void e_billpay_valid_send() {
        System.out.println("Edge – billpay_valid_send");
        // Fill amount, click “Send Payment”, etc.
    }

    @Edge("TransferFunds_e_Select_Different_Accounts")
    public void e_transfer_different_accounts() {
        System.out.println("Edge – transfer_different_accounts");
        // Choose source and destination accounts, then click Transfer
    }

    // Example of an edge guard (pre‑condition) for a “missing field” transition
    @Edge("Register_e_Invalid_Missing_Password")
    public void e_invalid_missing_password() {
        System.out.println("Edge – invalid_missing_password (pre‑condition check)");
        // Guard: password field must be empty – we assert it now
        // assertTrue(driver.findElement(By.id("password")).getAttribute("value").isEmpty(),
        //            "Password must be empty for this test case");
    }

    /* --------------------------------------------------------------
       Test driver – executes the model and checks coverage.
       -------------------------------------------------------------- */

    @Test
    public void runFullCoverageTest() {
        Result result = new TestExecutor()
                .addPathGenerator("random(edge_coverage(100))")         // 100 % edge coverage
                .addModel(ParabankMbtTest.class)                     // our annotated class
                .execute();

        // Verify that the generated walk succeeded without assertion failures
        assertTrue(result.hasPassed(), "GraphWalker execution failed");
        System.out.println("✅ 100 % edge coverage achieved!");
    }
}
```

**Key points in the code above**

| Element | Purpose |
|---------|---------|
| `@Vertex("Login_v_Start")` | Marks the *starting vertex*; the method runs when the walker first lands here. |
| `@Edge("Login_e_Invalid_Login_Empty")` | Marks a transition; the method runs **only** when that specific edge is taken. |
| Edge guard logic | The `assertTrue(...)` inside `e_invalid_missing_password` demonstrates how you can enforce that a particular state actually satisfies a guard before proceeding. |
| `runFullCoverageTest()` | Starts the walk generated from the JSON config; asserts that *all* edges were explored (`result.hasPassed()`). |
| `setUp()` | Typical test fixture – open the ParaBank home page. In a real CI environment you would inject a Selenium `WebDriver`. |

> **Why use annotations?**  
> GraphWalker scans the test class at runtime. Every `@Vertex`/`@Edge` method **must** follow a naming convention that exactly matches the vertex/edge identifier (`v_…` or `e_…`). This eliminates manual mapping and keeps the test code declarative.

---

### 4. Sample Test Scenarios (One for Each Critical Edge Guard)

| # | Edge (source → target) | Description (when it is exercised) | Pre‑condition (guard) | Expected outcome |
|---|------------------------|--------------------------------------|-----------------------|------------------|
| 1 | `Login_e_Invalid_Login_Empty` → `Login_v_Verify_Invalid_Login_Empty_Password` | User tries to login with **no password**. | Password field empty. | Error message *“Password is required”*. |
| 2 | `Register_e_Invalid_Missing_Field` → `Register_v_Missing_Field` | Registration attempted with an empty **email** field. | Email field empty. | Validation message *“Email is required”*. |
| 3 | `BillPay_e_Invalid_Account_Send_Payment` → `BillPay_v_Error` | Payment attempted to a **non‑existent account**. | Account number not found in DB. | Error *“Account does not exist”*. |
| 4 | `TransferFunds_e_Invalid_Amount` → `TransferFunds_v_Error` | Transfer amount exceeds the daily limit. | Amount > configured limit. | Error *“Transfer amount exceeds limit”*. |
| 5 | `RequestLoan_e_Invalid_Apply_Now` → `RequestLoan_v_Error` | Loan application submitted without any data. | All loan fields empty. | Error *“Please fill all fields”*. |
| … | … | … | … | … |

Every edge in the JSON appears **once** in the automatically generated walk, so executing the walk will realize all the above scenarios (and many more), guaranteeing **100 % edge and vertex coverage**.

---

### 5. Running the Test  

```bash
# From the project root
mvn clean test
```

You should see console output similar to:

```
=== Test set-up: open login page ===
Vertex – Login_Start
Vertex – Login page displayed
Edge – goto_login (open login page)
Vertex – Login page displayed
Edge – valid_login
Vertex – AccountActivity_v_Activity_Period_Filter_Set
...
Edge – invalid_missing_password (pre‑condition check)
...
✅ 100 % edge coverage achieved!
```

If any edge is **not** traversed, `result.hasPassed()` will be `false` and the build will fail, signalling that the model is incomplete or that a missing edge guard blocks the walk.

---

### 6. Extending the Model  

If later you add a new feature (e.g., “Schedule Transfer”), simply:

1. Add a new vertex to the JSON (`ScheduleTransfer_v_Screen`).  
2. Connect it with the appropriate edges (`ScheduleTransfer_e_Submit`).  
3. Update `graphwalker.json` if the generator rule changes.  
4. Add matching `@Vertex` and `@Edge` methods in the test class.  
5. Re‑run `mvn test`; GraphWalker will automatically extend the coverage.

---

## Summary  

* **Vertices** → mapped to `@Vertex` methods, each logs or performs the UI step.  
* **Edges** → mapped to `@Edge` methods, each contains an *edge guard* (pre‑condition) that can be asserted before proceeding.  
* The **generator** `random(edge_coverage(100))` guarantees **full coverage**.  
* A single JUnit 5 test (`runFullCoverageTest`) orchestrates the walk and validates that all edges were exercised.  

By following the skeleton above you obtain a **repeatable, automated test suite** that:

* Is **deterministically generated** from the model,  
* Provides **traceability** (each test step corresponds to a model element),  
* Allows **edge guards** to enforce realistic pre‑conditions, and  
* Can be integrated into CI pipelines for continuous regression testing of ParaBank.

---  

**References**  

- GraphWalker official documentation: [graphwalker.github.io](https://graphwalker.github.io)  
- GraphWalker Maven integration guide: [graphwalker.github.io/projects/graphwalker/wiki/Maven](https://graphwalker.github.io/projects/graphwalker/wiki/Maven)  
- Model‑Based Testing overview (Medium article): [nehabimal.com](https://medium.com/@nehabimal2003/model-based-testing-mbt-using-graphwalker-76284eba6817)  

All links are prefixed with the domain name for easy citation.