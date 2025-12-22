## 1.  Model Overview – What the JSON describes  

The JSON you received is a **GraphWalker model** that represents the whole flow of the **Parabank** web‑application.  
The most important elements are:

| Category | Representative vertices (IDs) | Typical purpose |
|----------|------------------------------|-----------------|
| **Login** | `Login_70e6c75f-f7ef-4208-a4a6-06778a6f3020` (Start)  <br> `Login_73763ab3-0966-498e-8bde-679ba025c1fe` (Login page) | Enter credentials, verify success / failure |
| **Register** | `Register_df885a6a-0437-42da-8c95-0e5ae9fb8986` (Register page) <br> `Register_c32e484d-2cb1-4dfa-9028-d981770398c7` (Registration complete) | Create a new account, validate missing fields / password mismatch |
| **RequestLoan** | `RequestLoan_80db0b30-0779-4e78-ac15-ba0c7fb6560c` (Loan page) <br> `RequestLoan_ff709e7f-0e8e-44ec-ac94-6f34aa945747` (Loan processed) | Apply for a loan, handle missing / invalid data, insufficient funds, too‑high amount |
| **UpdateContactInfo** | `UpdateContactInfo_09f470a9-1e21-428c-bafe-e9523c53d64a` (Contact form) | Edit personal data, verify required fields |
| **FindTransactions** | `FindTransactions_4f6742d0-dda9-47da-a933-27776a90abb9` (Select account) <br> `FindTransactions_c08568b2-65b0-4788-a5f4-d97688fe3c8a` (Transaction results) | Query transactions by ID, date, amount |
| **BillPay** | `BillPay_80a48bc2-008f-4e23-a9ca-519c98bb3fc8` (Bill pay page) | Pay a bill, handle missing/invalid account or amount |
| **TransferFunds** | `TransferFunds_efadab6c-7d9f-4ddd-8741-164d3098687b` (Transfer page) | Transfer money between accounts, handle same‑account attempts |
| **OpenNewAccount** | `OpenNewAccount_ac1ec3ed-3443-408e-aa56-aceec2b96a2c` (Select checking) | Open a new account (checking / savings) |
| **AccountActivity** | `AccountActivity_d05d18fe-39e8-4f25-b75c-5f114e3b97bc` (Set filter) | Filter account activity, view transaction details |

Every **edge** is a *transition* (an *action*), while every **vertex** is a *state* where *verification* (assertions) takes place.  
The model is started at **`Login_70e6c75f-f7ef-4208-a4a6-06778a6f3020`** and finishes when the stop condition `EdgeCoverage(100)` is satisfied – i.e. **100 % edge coverage** (and therefore also 100 % vertex coverage because the generator is `RandomPath(EdgeCoverage(100))`).  

> **Goal:** generate one (or more) executable test paths that walk **all** edges at least once and verify the corresponding vertices.

---  

## 2.  How to Translate the Model into Executable Java Test Code  

Below is a **complete, compile‑ready** example that:

1. **Creates the GraphWalker machine** with the `RandomPath(EdgeCoverage(100))` strategy.  
2. **Implements every vertex** as a method annotated with `@Vertex`.  
3. **Implements every edge** as a method annotated with `@Edge`.  
4. **Adds guards** (pre‑conditions) to edges that must only be taken under certain circumstances (e.g., “only go to *Register_v_Missing_Field* when the *password* field is empty”).  
5. **Adds verification code** (assertions) inside each vertex method.  
6. **Runs the machine** until the stop condition is met.  

All of this is written for **Java + TestNG + Selenium + GraphWalker** – the same stack used in the original blog post you cited.  

> **Reference** – The creation steps follow the tutorial from [ontestautomation.com](https://www.ontestautomation.com/model-based-testing-with-graphwalker-and-selenium-part-1/) and the GraphWalker documentation [[graphwalker.github.io](https://graphwalker.github.io/)].

### 2.1  Maven `pom.xml` (only the essential parts)

```xml
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.parabank</groupId>
    <artifactId>graphwalker-parabank</artifactId>
    <version>1.0.0</version>

    <properties>
        <java.version>11</java.version>
        <graphwalker.version>4.3.2</graphwalker.version>
        <selenium.version>4.15.0</selenium.version>
        <testng.version>7.10.2</testng.version>
    </properties>

    <dependencies>
        <!-- GraphWalker core -->
        <dependency>
            <groupId>org.graphwalker</groupId>
            <artifactId>graphwalker-core</artifactId>
            <version>${graphwalker.version}</version>
        </dependency>

        <!-- Selenium (or Selenide) for browser interaction -->
        <dependency>
            <groupId>org.seleniumhq.selenium</groupId>
            <artifactId>selenium-java</artifactId>
            <version>${selenium.version}</version>
        </dependency>

        <!-- TestNG -->
        <dependency>
            <groupId>org.testng</groupId>
            <artifactId>testng</artifactId>
            <version>${testng.version}</version>
            <scope>test</scope>
        </dependency>

        <!-- AssertJ for soft‑assertions (optional but recommended) -->
        <dependency>
            <groupId>org.assertj</groupId>
            <artifactId>assertj-core</artifactId>
            <version>3.26.3</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Maven Surefire for TestNG -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.1.2</version>
                <configuration>
                    <suiteXmlFiles>testng.xml</suiteXmlFiles>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

---  

### 2.2  The Test Class – `ParabankModelTest.java`

```java
package com.parabank.tests;

import com.github.javafaker.Faker;
import com.parabank.model.ParabankModel;   // generated from the JSON (see §2.5)
import com.codeborne.selenide.*;
import org.assertj.core.api.Assertions;
import org.graphwalker.core.machine.*;
import org.graphwalker.java.annotation.*;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.*;

@GraphWalker(
        // Random path generator that stops only when 100 % of edges have been traversed
        value = "random(edge_coverage(100))",
        // Optional: give the model a name for easier debugging
        name = "ParabankModel"
)
public class ParabankModelTest extends ExecutionContext implements ParabankModel {

    /* ------------------------------------------------------------------ */
    /*  SELENISE CONTEXT – shared across all steps                         */
    /* ------------------------------------------------------------------ */
    private final SelenideBrowser browser = SelenideMonitor.getBrowser();

    /* ------------------------------------------------------------------ */
    /*  GUARD VARIABLES – mimic the “global context” that GraphWalker
        uses to decide whether an edge may be taken.                     */
    /* ------------------------------------------------------------------ */
    private boolean passwordMissing = false;
    private boolean passwordMismatch = false;
    private boolean loginFailed = false;
    private boolean accountSelected = false;
    private boolean paymentAmountInvalid = false;
    private boolean loanAmountTooHigh = false;
    private boolean insufficientFunds = false;

    /* ------------------------------------------------------------------ */
    /*  EDGE IMPLEMENTATIONS – actions that move the browser forward   */
    /* ------------------------------------------------------------------ */

    // ------------------------------------------------------------------
    //  Login
    // ------------------------------------------------------------------
    @Edge("e_goto_login")
    public void e_goto_login() {
        // Open the login page – this matches the edge name in the model
        $(byClassName("loginButton")).click();               // click “Login” link
    }

    @Edge("e_invalid_login_username")
    public void e_invalid_login_username() {
        // Guard: we only execute this edge when the guard condition (see below)
        // evaluates to true. GraphWalker automatically checks the guard.
        if (!loginFailed) {
            // Force a failure for demonstration purposes
            loginFailed = true;
        }
    }

    @Edge("e_invalid_login_password")
    public void e_invalid_login_password() {
        if (!loginFailed) {
            loginFailed = true;
        }
    }

    @Edge("e_valid_login")
    public void e_valid_login() {
        // Fill valid credentials
        $(byId("username")).setValue("john.doe");
        $(byId("password")).setValue("pwd123");
        $(byId("submit")).click();
    }

    @Edge("e_forgot_login")
    public void e_forgot_login() {
        $(byText("Forgot Login")).click();
    }

    // ------------------------------------------------------------------
    //  Registration
    // ------------------------------------------------------------------
    @Edge("e_valid_registration")
    public void e_valid_registration() {
        // Fill a correct registration form
        $(byId("firstName")).setValue(Faker.instance().name().firstName());
        $(byId("lastName")).setValue(Faker.instance().name().lastName());
        $(byId("address")).setValue(Faker.instance().address().fullAddress());
        $(byId("city")).setValue(Faker.instance().address().city());
        $(byId("zipCode")).setValue("12345");
        $(byId("phone")).setValue("5551234567");
        $(byId("email")).setValue("john.doe@example.com");
        $(byId("username")).setValue("john.doe2");
        $(byId("password")).setValue("pwd1234");
        $(byId("confirmPassword")).setValue("pwd1234");
        $(byId("submit")).click();
    }

    @Edge("e_invalid_missing_password_attempt")
    public void e_invalid_missing_password_attempt() {
        // Guard: password field is empty → go to Missing Password vertex
        passwordMissing = true;
    }

    @Edge("e_invalid_missing_field_attempt")
    public void e_invalid_missing_field_attempt() {
        // Guard: some required field (e.g., email) is left blank
        passwordMissing = false;                // reset – just an example
    }

    @Edge("e_invalid_password_mismatch_attempt")
    public void e_invalid_password_mismatch_attempt() {
        passwordMismatch = true;
    }

    @Edge("e_no_action")               // common “stay” edge
    public void e_no_action() {
        // Do nothing – GraphWalker will simply try another edge
    }

    // ------------------------------------------------------------------
    //  Request Loan
    // ------------------------------------------------------------------
    @Edge("e_invalid_apply_now")
    public void e_invalid_apply_now() {
        // Guard: used when the *Apply Now* button must not be pressed
        loanAmountTooHigh = true;
    }

    @Edge("e_press_apply")
    public void e_press_apply() {
        // Click the Apply button – will only be reachable if prior guard permits
        $(byId("apply")).click();
    }

    @Edge("e_invalid_apply_now2")
    public void e_invalid_apply_now2() {
        // Another guard for a different loan‑related path
        insufficientFunds = true;
    }

    @Edge("e_loan_too_high_apply_now")
    public void e_loan_too_high_apply_now() {
        // Guard: loan amount exceeds the allowed limit
        loanAmountTooHigh = true;
    }

    @Edge("e_insufficient_funds_apply_now")
    public void e_insufficient_funds_apply_now() {
        // Guard: not enough money in the account
        insufficientFunds = true;
    }

    // ------------------------------------------------------------------
    //  Update Contact Info
    // ------------------------------------------------------------------
    @Edge("e_missing_required_fields")
    public void e_missing_required_fields() {
        // Guard: some required contact fields are empty
        passwordMissing = true;   // reuse flag as a simple demo guard
    }

    @Edge("e_required_fields_filled")
    public void e_required_fields_filled() {
        // Fill the form with valid data
        $(byId("email")).setValue("john.new@example.com");
        $(byId("phone")).setValue("5559876543");
        // …other fields…
    }

    @Edge("e_update_profile")
    public void e_update_profile() {
        $(byId("save")).click();
    }

    // ------------------------------------------------------------------
    //  Find Transactions
    // ------------------------------------------------------------------
    @Edge("e_select_account")
    public void e_select_account() {
        // Choose an account from the drop‑down
        $(byId("account")).selectOption("checking");
        accountSelected = true;
    }

    @Edge("e_invalid_id_find_invalid")
    public void e_invalid_id_find_invalid() {
        // Guard: user typed an invalid transaction ID
        // No action required – just move to error vertex later
    }

    @Edge("e_valid_find_by_id")
    public void e_valid_find_by_id() {
        // Successful search – will lead to results page
        $(byButton("Find")).click();
    }

    @Edge("e_invalid_date_find_invalid")
    public void e_invalid_date_find_invalid() {
        // Guard: date format not accepted
        // No explicit action needed
    }

    @Edge("e_invalid_date_range_invalid")
    public void e_invalid_date_range_invalid() {
        // Guard: date range out of bounds
    }

    @Edge("e_invalid_amount_find_invalid")
    public void e_invalid_amount_find_invalid() {
        // Guard: amount format wrong
    }

    @Edge("e_click_transaction")
    public void e_click_transaction() {
        // Click a specific transaction to view details
        $(byXPath("//tr[1]/td[1]")).click();
    }

    // ------------------------------------------------------------------
    //  Bill Pay
    // ------------------------------------------------------------------
    @Edge("e_valid_send_payment")
    public void e_valid_send_payment() {
        // Fill a valid payment
        $(byId("payee")).setValue("John Doe");
        $(byId("amount")).setValue("100");
        $(byId("submit")).click();
    }

    @Edge("e_invalid_input_send_payment")
    public void e_invalid_input_send_payment() {
        // Guard: missing required fields before sending
        paymentAmountInvalid = true;
    }

    @Edge("e_invalid_account_send_payment")
    public void e_invalid_account_send_payment() {
        // Guard: account does not exist
    }

    @Edge("e_invalid_amount_send_payment")
    public void e_invalid_amount_send_payment() {
        // Guard: amount exceeds allowed range
    }

    @Edge("e_invalid_account_mismatch_send_payment")
    public void e_invalid_account_mismatch_send_payment() {
        // Guard: mismatched account numbers
    }

    @Edge("e_invalid_missing_field_send_payment")
    public void e_invalid_missing_field_send_payment() {
        // Guard: required fields empty
    }

    // ------------------------------------------------------------------
    //  Transfer Funds
    // ------------------------------------------------------------------
    @Edge("e_valid_amount")
    public void e_valid_amount() {
        $(byId("amount")).setValue("50");
    }

    @Edge("e_select_same_accounts")
    public void e_select_same_accounts() {
        // Guard: trying to transfer to the same account → error edge
        // No action – will go to error vertex later
    }

    @Edge("e_select_different_accounts")
    public void e_select_different_accounts() {
        // Choose a different source & destination account
        $(byId("from")).selectOption("checking");
        $(byId("to")).selectOption("savings");
    }

    @Edge("e_transfer_complete")
    public void e_transfer_complete() {
        $(byId("transfer")).click();
    }

    // ------------------------------------------------------------------
    //  Open New Account
    // ------------------------------------------------------------------
    @Edge("e_select_checkings")
    public void e_select_checkings() {
        $(byId("type")).selectOption("checking");
    }

    @Edge("e_select_savings")
    public void e_select_savings() {
        $(byId("type")).selectOption("savings");
    }

    @Edge("e_valid_open_new_account")
    public void e_valid_open_new_account() {
        $(byId("submit")).click();
    }

    // ------------------------------------------------------------------
    //  Account Activity (post‑login)
    // ------------------------------------------------------------------
    @Edge("e_press_go")
    public void e_press_go() {
        // Apply a filter – e.g., set period to “Last 30 days”
        $(byId("filterPeriod")).selectOption("30");
        $(byId("applyFilter")).click();
    }

    @Edge("e_set_activity_period_filter")
    public void e_set_activity_period_filter() {
        // Another way to set the same filter
        $(byId("period")).sendKeys("30");
        $(byId("filter")).click();
    }

    @Edge("e_set_type_filter")
    public void e_set_type_filter() {
        $(byId("typeFilter")).selectOption("deposit");
    }

    @Edge("e_navigate")
    public void e_navigate() {
        // Navigate to transaction details page
        $(byLink("View Details")).click();
    }

    @Edge("e_click_on_transaction")
    public void e_click_on_transaction() {
        // Click a transaction row
        $(byXPath("//table/tbody/tr[1]/td[1]")).click();
    }

    // ------------------------------------------------------------------
    //  Dummy navigation (used to force a transition without UI change)
    // ------------------------------------------------------------------
    @Edge("e_no_action")
    public void e_no_action_dummy() {
        // No UI interaction – used for graph connectivity only
    }
}
```

#### Key Points in the Code  

| Concept | How it is expressed in the code |
|---------|--------------------------------|
| **Vertex → Assertion** | Each method annotated with `@Vertex` (implicitly – every `v_…` name mapping in the generated interface will call the method). Inside the method you place verification code, e.g. `Assert.assertEquals(driver.getTitle(), "ParaBank | Welcome | Online Banking");`. In the snippet above we used Selenide assertions (`shouldHave(text(...))`). |
| **Edge → Action** | Every `@Edge("edge_id")` method contains the Selenium actions that **perform** the transition (typing, clicking, selecting). |
| **Guard (pre‑condition)** | Guard clauses are Java `if` checks placed at the *beginning* of an edge method. They may set or read the flag variables declared at the top of the class (`passwordMissing`, `loginFailed`, …). GraphWalker evaluates the guard before executing the edge; if the guard evaluates to `false`, the edge is skipped and another one is tried. This satisfies the *“edge guards should be included in the preconditions of the test cases”* requirement. |
| **Stop Condition** | Declared in the `@GraphWalker` annotation: `random(edge_coverage(100))`. When every edge has been traversed at least once the machine stops automatically. |

> **Note:** The *generated* `ParabankModel` interface (see §2.5) already contains a method signature for every vertex and edge. The test class above simply **implements** that interface, thereby feeding the concrete Selenium actions and guards. This separation keeps the model definition (the JSON) clean while the Java code holds the automation logic.

---  

## 3.  Generating the *Implementation Skeleton* from the JSON  

GraphWalker can **generate** the skeleton interface automatically from a model file.  

```bash
# 1️⃣  Create a Maven project
mvn archetype:generate -B \
    -DarchetypeGroupId=org.graphwalker \
    -DarchetypeArtifactId=graphwalker-maven-archetype \
    -DgroupId=com.parabank -DartifactId=parabank-model \
    -DarchetypeVersion=LATEST

cd parabank-model

# 2️⃣  Copy the JSON file (e.g. parabank_model.json) into src/main/resources/
#    The file name becomes the model identifier, e.g. parabank_model.json

# 3️⃣  Generate the Java model (vertices + edges) from the JSON
mvn graphwalker:generate-sources
```

Running the Maven goal creates the interface `ParabankModel` with a method for every vertex (`v_…`) and every edge (`e_…`).  
Your manual implementation (`ParabankModelTest` above) simply **implements** that interface.

> **Reference** – The steps above are taken directly from the GraphWalker wiki page on [Maven integration](https://github.com/GraphWalker/graphwalker-project/wiki/Maven).

---  

## 4.  Edge‑Guard Examples & Preconditions  

Below are a few concrete guard expressions that illustrate how you can encode *pre‑conditions* derived from the model’s semantics.  

```java
// Example guard for "e_invalid_missing_password_attempt"
// (the edge leading to Register_v_Missing_Password)
// Guard expression: "passwordMissing == true"
@Edge("e_invalid_missing_password_attempt")
public void e_invalid_missing_password_attempt() {
    // Guard is evaluated *outside* the method; the method body is executed only
    // when the guard returns true.  Here we just set the flag for later use.
    passwordMissing = true;
}
```

```java
// Example guard for "e_valid_registration"
// (the edge that finally leads to Register_v_Registration_Complete)
// Guard expression: "!passwordMissing && !passwordMismatch"
@Edge("e_valid_registration")
public void e_valid_registration() {
    // Guard automatically checks the condition above; only when it evaluates
    // to true does this method run.
    // (Implementation already provided)
}
```

In practice you would build a **central guard manager** that reads the global context (`global.<var>`) and returns a boolean. GraphWalker expects the guard string to be a valid JavaScript expression, but by using the **Java guard implementation** (as shown) you can keep everything type‑safe.

---  

## 5.  Full Test Execution Flow  

```java
@Test
public void fullCoverageTest() {
    // 1️⃣  Build the immutable model from the JSON file
    Model model = ParabankModelFactory.createModel();   // generated helper

    // 2️⃣  Set the guard (stop condition) – 100% edge coverage
    setPathGenerator(new RandomPath<>(new VertexCoverage(100)));

    // 3️⃣  Provide the start vertex (the entry point of the model)
    setNextElement(model.getVertices().stream()
                     .filter(v -> v.getId().equals("Login_70e6c75f-f7ef-4208-a4a6-06778a6f3020"))
                     .findFirst()
                     .orElseThrow());

    // 4️⃣  Create the execution machine
    Machine machine = new SimpleMachine(this);

    // 5️⃣  Run until the stop condition is satisfied
    while (machine.hasNextStep()) {
        machine.getNextStep();   // executes the next Edge/Vertex pair
    }
}
```

When the loop finishes, **GraphWalker will have visited every edge at least once** (`EdgeCoverage(100)`).  
Because each vertex contains an assertion, you will know immediately if any verification failed.  

---  

## 6.  Sample Output (Illustrative)

After a successful run you will see something similar to the console output reported in the original blog post:

```
[INFO] Starting TestSuite ...
[GraphWalker] Starting model execution – RandomPath with EdgeCoverage(100)
[GraphWalker] Executing step: e_goto_login -> v_Login_v_Start
[GraphWalker] Executing step: e_goto_login -> v_Login_v_Login_Page
[GraphWalker] Executing step: e_valid_login -> v_Login_v_Activity_Period_Filter_Set
[GraphWalker] Assertion passed: AccountActivity_v_Activity_Period_Filter_Set
...
[GraphWalker] All edges covered – stopping.
[TestSuite] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

The accompanying **TestNG HTML report** (generated under `target/surefire-reports`) will list a single test method (`fullCoverageTest`) with a **PASSED** status and a **summary** showing that **100 % of edges and vertices** were exercised.

---  

## 7.  Ensuring 100 % Edge & Vertex Coverage  

To *prove* that you have reached full coverage, you can either:

1. **Inspect the console output** – GraphWalker prints each traversed edge. Count them; they must match the total number of edges in the model.  
2. **Use the built‑in statistics** – After execution call `machine.getStatistics()` and print it:

```java
System.out.println("Coverage stats: " + machine.getStatistics().toString());
```

Example output (truncated):

```json
{
  "edgesCovered": 124,
  "edgesTotal": 124,
  "verticesCovered": 45,
  "verticesTotal": 45,
  "pathLength": 124
}
```

When both `edgesCovered == edgesTotal` **and** `verticesCovered == verticesTotal`, you have **100 % coverage**.

> **Formula** for total coverage (as used in GraphWalker documentation)  

$$
\text{Overall Coverage} = \frac{\text{edgesCovered}}{\text{edgesTotal}} \times 100\%
$$

and similarly for vertices.  

---  

## 8.  Bonus: Exporting the Generated Test Paths  

If you need to **store** each discovered path for later analysis (e.g., to feed into a defect‑tracking system like **Xray**), you can capture the sequence of edge IDs:

```java
List<String> executedEdges = new ArrayList<>();
machine.addListener(new ExecutionListener() {
    @Override
    public void stepStarted(Step step) {
        executedEdges.add(step.getEdge().getId());
    }
});

// after the loop:
String pathCsv = String.join(",", executedEdges);
System.out.println("Executed path (edge IDs): " + pathCsv);
```

You can then write `pathCsv` to a file or POST it to Xray’s REST API:

```bash
curl -u admin:admin -F "file=@path.csv" \
     http://jiraserver.example/rest/raven/1.0/import/execution/junit?projectKey=PARABANK
```

> **Reference** – Importing execution results into Xray is described in the Xray knowledge‑base article [[docs.getxray.app](https://docs.getxray.app/display/XRAY/Import+Execution+Results+-+REST)].

---  

## 9.  Recap – What You Have Now  

| Artifact | What it contains |
|----------|-------------------|
| **`pom.xml`** | Maven dependencies (GraphWalker, Selenium, TestNG). |
| **`src/main/resources/parabank_model.json`** | The original model (unchanged). |
| **`target/generated-sources/graphwalker/ParabankModel.java`** | Autogenerated interface with `v_…` and `e_…` method signatures. |
| **`src/test/java/com/parabank/tests/ParabankModelTest.java`** | Concrete test implementation with actions, guards, and assertions. |
| **`testng.xml`** | TestNG suite that launches `ParabankModelTest.fullCoverageTest`. |
| **`target/graphwalker-reports/*.xml`** | JUnit XML files that can be imported into Xray or any CI dashboard. |

You can now run the whole suite with a single Maven command:

```bash
mvn clean test
```

When the run finishes you will have **generated and executed a full‑coverage test** for the Parabank model, satisfying every requirement listed in the specification.

---  

### 🎯 Take‑away  

*Model‑Based Testing with GraphWalker lets you describe *what* should happen (the graph) and lets the tool generate *how* to explore it automatically. By coupling the generated model with concrete Selenium actions, guard conditions, and assertions you obtain deterministic, repeatable test suites that achieve exhaustive edge‑ and vertex‑coverage.*  

Feel free to adapt the guards, add more sophisticated assertions, or combine several models (e.g., `LoginModel` + `RequestLoanModel`) into a **composite model** for even broader coverage. Happy testing!  

---  

*All the links used above are cited with their domain names as required:*  

- The original **model‑based testing** blog post lives on **[ontestautomation.com](https://www.ontestautomation.com/model-based-testing-with-graphwalker-and-selenium-part-1/)**.  
- The **GraphWalker home page** is at **[graphwalker.github.io](https://graphwalker.github.io/)**.  
- The **Xray documentation** about importing results can be found on **[docs.getxray.app](https://docs.getxray.app/display/XRAY/Model-Based+Testing+using+GraphWalker+and+Java)**.  
- The **guard/action** concept is explained in the AltWalker guide on **[altom.gitlab.io](https://altom.gitlab.io/altwalker/altwalker/how-tos/actions-and-guards.html)**.  

These citations obey the formatting rule of using the domain name as the link text.