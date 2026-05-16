---
description: "Use when designing, implementing, or modifying any UI/UX component — screens, views, dialogs, forms, widgets, panels, windows, pages, CLI commands, terminal prompts, interactive command-line tools, TUI (terminal user interface), or any layer that renders data to the user or handles user input. Enforces the MVP (Model-View-Presenter) pattern: passive View interface, Presenter as sole orchestrator, Model with no UI dependencies. Applies to all programming languages and UI frameworks including graphical, web, mobile, desktop, and CLI/terminal."
---

# MVP (Model-View-Presenter) Pattern

Apply this pattern to every UI component regardless of programming language or framework (desktop, mobile, web, embedded, terminal UI, etc.).

---

## 1. Core Philosophy

MVP divides a UI component into three strictly separated roles:

- **Model** — owns data and business logic. Knows nothing about the UI.
- **View** — displays data and forwards user input. Contains zero logic.
- **Presenter** — the sole orchestrator. Reacts to View events, queries/mutates the Model, and pushes updated data back to the View.

**The fundamental rule**: The View and the Model **never communicate directly**. All flow passes through the Presenter.

```
User Input ──► View ──► Presenter ──► Model
                 ◄──────────────────────
```

---

## 2. Component Responsibilities

### Model

**Must:**
- Hold application state relevant to the feature
- Implement all business logic and validation
- Expose data via well-named accessors or a clean data structure
- Be independently testable with no UI dependency

**Must not:**
- Import or reference any UI framework type
- Trigger UI updates directly
- Know which screen or component is consuming it

```
// ✅ Good — pure data + logic, no UI awareness
class UserModel:
    data: User
    function validate_email(email) -> bool
    function save() -> Result

// ❌ Bad — Model aware of UI
class UserModel:
    view_reference: LoginView       // never
    function update_label(text)     // never
```

---

### View

**Must:**
- Be defined as an **interface / protocol / abstract type** (see Section 3)
- Expose methods for the Presenter to push display data (`show_user(user)`, `set_error(msg)`, `show_loading()`)
- Expose event hooks or delegate calls back to the Presenter (`on_submit_clicked()`, `on_text_changed(value)`)
- Contain **zero business logic** — no if/else on domain data, no validation, no formatting beyond display

**Must not:**
- Hold a reference to the Model
- Call any Presenter method except to forward raw user input
- Make decisions about what data to show

```
// ✅ Good — passive, dumb interface
interface ILoginView:
    function show_error(message: string)
    function show_loading(is_loading: bool)
    function navigate_to_home()
    event on_login_clicked(username: string, password: string)

// ❌ Bad — View with logic
class LoginView:
    function on_login_clicked():
        if self.username == "admin":   // logic belongs in Presenter/Model
            navigate_to_home()
```

---

### Presenter

**Must:**
- Hold a reference to the **View interface** (not the concrete widget)
- Hold a reference to the Model (or a service/repository abstraction)
- React to all user input events forwarded from the View
- Coordinate: read/write Model, then call View methods to reflect the result
- Be the **only** place where UI-related decisions are made ("if login fails → show error")

**Must not:**
- Import or use concrete UI framework types (widgets, controls, DOM elements)
- Contain raw data persistence logic (delegate to Model/repository)
- Grow into a God Object — split into multiple Presenters if a screen has distinct independent areas

```
// ✅ Good — orchestrates, imports no UI framework
class LoginPresenter:
    constructor(view: ILoginView, model: AuthModel)

    function on_login_clicked(username, password):
        view.show_loading(true)
        result = model.authenticate(username, password)
        view.show_loading(false)
        if result.success:
            view.navigate_to_home()
        else:
            view.show_error(result.error_message)

// ❌ Bad — Presenter doing UI framework work
class LoginPresenter:
    function on_login_clicked():
        button.set_enabled(false)        // direct widget manipulation
        label.set_text("Logging in...")  // coupled to concrete widget
```

---

## 3. The View Interface Contract

Always define the View as an **interface, protocol, or abstract base class** — never couple the Presenter to a concrete widget or component.

**Why:** This is what makes the Presenter unit-testable (inject a mock View) and what makes the View swappable (swap web View for mobile View, or real View for test double).

```
// Interface definition (adapt syntax to your language)
interface IUserProfileView:
    function display_profile(name: string, avatar_url: string, bio: string)
    function show_save_confirmation()
    function show_validation_error(field: string, message: string)
    function set_save_button_enabled(enabled: bool)
    event on_save_clicked(name: string, bio: string)
    event on_avatar_clicked()

// Concrete View implements the interface
class UserProfileScreen implements IUserProfileView:
    // real widget/DOM/framework code here

// Test double implements the same interface
class FakeUserProfileView implements IUserProfileView:
    // recorded calls, stubs for assertions
```

**Rules for the interface:**
- Methods must be named from the View's perspective, not the Presenter's: `show_error(msg)` not `presenter_sent_error(msg)`
- Avoid passing complex domain objects into View methods — pass primitives or simple display-only structs; the View must not be able to call business logic on what it receives
- Events/callbacks must carry only raw input values, not pre-processed domain objects

---

## 4. Communication & Dependency Rules

```
        ┌──────────┐         ┌───────────────┐         ┌──────────┐
        │  Model   │◄────────│   Presenter   │────────►│  IView   │
        └──────────┘         └───────────────┘         └────┬─────┘
                                                             │ implements
                                                        ┌────▼─────┐
                                                        │ ConcreteView │
                                                        └──────────┘
```

**Allowed dependencies:**

| Component | May depend on |
|---|---|
| Model | Nothing UI-related; other domain models/services/repositories |
| Presenter | `IView` interface; Model |
| ConcreteView | `IView` interface (implements it); UI framework; Presenter (to wire events) |

**Forbidden:**

| ❌ Never do this | Why |
|---|---|
| View holds a reference to Model | Bypasses Presenter; breaks separation |
| Presenter imports a UI framework type | Presenter becomes untestable without a running UI runtime |
| Model calls back into View | Inverts control; Model becomes UI-aware |
| Presenter directly manipulates widgets | Couples Presenter to concrete UI; breaks testability |

**Dependency injection:** Wire everything at the composition root (app entry point, factory, DI container). The Presenter receives its View and Model via constructor injection — never creates them itself.

---

## 5. Naming Conventions

Use consistent naming so that MVP roles are immediately obvious:

| Role | Convention | Examples |
|---|---|---|
| View interface | `I{Feature}View` | `ILoginView`, `IUserProfileView`, `ICheckoutView` |
| Concrete View | `{Feature}View`, `{Feature}Screen`, `{Feature}Page` | `LoginView`, `UserProfileScreen`, `CheckoutPage` |
| Presenter | `{Feature}Presenter` | `LoginPresenter`, `UserProfilePresenter`, `CheckoutPresenter` |
| Model / domain data | `{Feature}Model`, `{Noun}` | `AuthModel`, `UserProfileModel`, `CartItem` |
| View methods (push) | verb + noun: `show_`, `display_`, `set_`, `hide_`, `navigate_to_` | `show_error()`, `display_results()`, `set_loading()` |
| View events (pull) | `on_{noun}_{verb}` | `on_login_clicked`, `on_search_changed`, `on_item_selected` |

---

## 6. Anti-patterns

### ❌ Fat View (logic in the View)

```
// ❌ Bad
class OrderView:
    function on_submit_clicked():
        if cart.total > 1000:
            apply_discount(0.1)        // business logic in View
        if user.is_guest:
            show_login_prompt()        // conditional logic in View
        else:
            submit_order()
```

```
// ✅ Good
class OrderView:
    function on_submit_clicked():
        presenter.on_submit_clicked()  // delegate all decisions to Presenter

class OrderPresenter:
    function on_submit_clicked():
        if model.qualifies_for_discount():
            model.apply_discount(0.1)
        if model.user_is_guest():
            view.show_login_prompt()
        else:
            result = model.submit_order()
            result.success ? view.show_confirmation() : view.show_error(result.message)
```

---

### ❌ Model-Aware View

```
// ❌ Bad — View directly queries the Model
class ProfileView:
    constructor(model: UserModel)   // View must NOT know about Model
    function refresh():
        label.set_text(model.get_full_name())
```

```
// ✅ Good — View only knows about its interface
class ProfileView implements IProfileView:
    function display_name(full_name: string):
        label.set_text(full_name)    // receives primitives, no Model reference
```

---

### ❌ Fat Presenter (God Object)

When a Presenter handles more than one cohesive feature area, split it.

```
// ❌ Bad — one Presenter for an entire dashboard
class DashboardPresenter:
    on_chart_filter_changed()
    on_user_table_row_selected()
    on_notification_dismissed()
    on_settings_save_clicked()
    // ... 40 more methods
```

```
// ✅ Good — one Presenter per cohesive feature area
class ChartPresenter ...
class UserTablePresenter ...
class NotificationPresenter ...
class SettingsPresenter ...
// Each wired to its own IView sub-interface
```

---

### ❌ Presenter Importing UI Framework

```
// ❌ Bad
import QtWidgets           // UI framework in Presenter
import android.widget.Button

class LoginPresenter:
    function on_login_clicked():
        submit_button.setEnabled(false)   // direct widget access
```

```
// ✅ Good
class LoginPresenter:
    function on_login_clicked():
        view.set_submit_button_enabled(false)   // via View interface only
```

---

## 7. Testability

MVP's primary benefit is that the **Presenter is fully unit-testable** with no running UI, no framework, and no rendering engine.

**How to test a Presenter:**
1. Create a **mock/fake View** that implements `IView` and records all calls
2. Create a **mock/fake Model** (or use a real one for integration-style tests)
3. Inject both into the Presenter
4. Fire events (`presenter.on_login_clicked("alice", "secret")`)
5. Assert on what the View received (`assert fake_view.last_error == "Invalid password"`)

```
// Test example (pseudocode)
test "login with wrong password shows error":
    fake_view = FakeLoginView()
    mock_auth  = MockAuthModel(returns_failure_for: "wrong_password")
    presenter  = LoginPresenter(view: fake_view, model: mock_auth)

    presenter.on_login_clicked(username: "alice", password: "wrong_password")

    assert fake_view.shown_error == "Invalid credentials"
    assert fake_view.navigation_target == null   // did NOT navigate

test "login success navigates to home":
    fake_view = FakeLoginView()
    mock_auth  = MockAuthModel(returns_success_for: "correct_password")
    presenter  = LoginPresenter(view: fake_view, model: mock_auth)

    presenter.on_login_clicked(username: "alice", password: "correct_password")

    assert fake_view.navigation_target == "home"
    assert fake_view.shown_error == null
```

**What NOT to test in Presenter tests:**
- Rendering/layout details (that's the ConcreteView's responsibility)
- Framework widget state (button color, font size)

**What to test in ConcreteView tests (UI/integration tests):**
- That events are wired and forwarded to the Presenter correctly
- That display methods produce the correct visual output

---

## 8. Applicability Scope

Apply MVP to **every unit of UI that has behavior**:

| Apply MVP | Skip MVP |
|---|---|
| Login / registration screen | Static display-only label |
| Search results page | Pure layout/styling component with no data |
| Settings form | Icon or image asset |
| List / table with selection or actions | Trivial pass-through wrapper |
| Dialog with confirmation / cancellation | |
| Dashboard panel with filters | |
| Wizard / multi-step form | |
| Any component that reads user input | |
| **CLI**: interactive prompts, multi-step wizards, menus | **CLI**: single one-shot script with no user interaction |
| **CLI**: commands with rich formatted output | **CLI**: simple batch processing utility |
| **TUI**: ncurses / `rich` / `textual`-style apps | |

For multi-screen flows, each screen gets its own Presenter. A shared data flow (e.g., a wizard that accumulates state across steps) should use a shared Model, not a shared Presenter.

### CLI / Terminal Applications

MVP applies to CLI apps, but the interaction model is **sequential/request-driven** rather than event-driven:
- The Presenter asks the View for input synchronously (`value = view.prompt_input("Search query: ")`), drives the Model, then writes output back to the View
- The View interface wraps `stdin`/`stdout`/`stderr` — concrete View uses `print()` / `input()` / ANSI codes; fake View records calls for tests
- Navigation (`navigate_to_home()`) becomes `view.exit()` or `view.show_next_screen(name)`

```
// CLI View interface example
interface ISearchCliView:
    function prompt_query() -> string
    function display_results(results: list[string])
    function print_error(message: string)
    function print_info(message: string)

// Concrete View — real terminal
class SearchCliView implements ISearchCliView:
    function prompt_query() -> string:
        return stdin.read_line("Enter search query: ")
    function display_results(results: list[string]):
        for result in results: stdout.write_line(result)

// Fake View — for unit tests, no terminal needed
class FakeSearchCliView implements ISearchCliView:
    captured_prompt_calls: int = 0
    displayed_results: list[string] = []
    function prompt_query() -> string:
        captured_prompt_calls += 1
        return "stubbed query"
    function display_results(results: list[string]):
        displayed_results = results
```
