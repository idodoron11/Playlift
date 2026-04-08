---
name: refactor
description: 'Surgical code refactoring to improve maintainability without changing behavior. Covers extracting functions, renaming variables, breaking down god functions, improving type safety, eliminating code smells, and applying design patterns. Less drastic than repo-rebuilder; use for gradual improvements.'
license: MIT
---

# Refactor

## Overview

Improve code structure and readability without changing external behavior. Refactoring is gradual evolution, not revolution. Use this for improving existing code, not rewriting from scratch.

> **Before you begin**: Take a deep breath, and review all coding guidelines in `.github/instructions/*.md` and `.github/copilot-instructions.md`, then review all the code carefully and make refactorings if needed.

## When to Use

Use this skill when:

- Code is hard to understand or maintain
- Functions/classes are too large
- Code smells need addressing
- Adding features is difficult due to code structure
- User asks "clean up this code", "refactor this", "improve this"

---

## Refactoring Principles

### The Golden Rules

1. **Behavior is preserved** - Refactoring doesn't change what the code does, only how
2. **Small steps** - Make tiny changes, test after each
3. **Version control is your friend** - One change at a time, one commit at a time: review changes with the user and get their approval before committing, then commit before moving to the next change
4. **Tests are essential** - Without tests, you're not refactoring, you're editing
5. **One thing at a time** - Don't mix refactoring with feature changes

### When NOT to Refactor

```
- Code that works and won't change again (if it ain't broke...)
- Critical production code without tests (add tests first)
- When you're under a tight deadline
- "Just because" - need a clear purpose
```

---

## Common Code Smells & Fixes

### 1. Long Method/Function

```diff
# BAD: 200-line function that does everything
- async def process_order(order_id):
-     # 50 lines: fetch order
-     # 30 lines: validate order
-     # 40 lines: calculate pricing
-     # 30 lines: update inventory
-     # 20 lines: create shipment
-     # 30 lines: send notifications

# GOOD: Broken into focused functions
+ async def process_order(order_id: str) -> dict:
+     order = await fetch_order(order_id)
+     validate_order(order)
+     pricing = calculate_pricing(order)
+     await update_inventory(order)
+     shipment = await create_shipment(order)
+     await send_notifications(order, pricing, shipment)
+     return {"order": order, "pricing": pricing, "shipment": shipment}
```

### 2. Duplicated Code

```diff
# BAD: Same logic in multiple places
- def calculate_user_discount(user):
-     if user.membership == "gold":
-         return user.total * 0.2
-     if user.membership == "silver":
-         return user.total * 0.1
-     return 0
-
- def calculate_order_discount(order):
-     if order.user.membership == "gold":
-         return order.total * 0.2
-     if order.user.membership == "silver":
-         return order.total * 0.1
-     return 0

# GOOD: Extract common logic
+ MEMBERSHIP_DISCOUNT_RATES: dict[str, float] = {"gold": 0.2, "silver": 0.1}
+
+ def get_membership_discount_rate(membership: str) -> float:
+     return MEMBERSHIP_DISCOUNT_RATES.get(membership, 0.0)
+
+ def calculate_user_discount(user) -> float:
+     return user.total * get_membership_discount_rate(user.membership)
+
+ def calculate_order_discount(order) -> float:
+     return order.total * get_membership_discount_rate(order.user.membership)
```

### 3. Large Class/Module

```diff
# BAD: God object that knows too much
- class UserManager:
-     def create_user(self): ...
-     def update_user(self): ...
-     def delete_user(self): ...
-     def send_email(self): ...
-     def generate_report(self): ...
-     def handle_payment(self): ...
-     def validate_address(self): ...
-     # 50 more methods...

# GOOD: Single responsibility per class
+ class UserService:
+     def create(self, data): ...
+     def update(self, user_id, data): ...
+     def delete(self, user_id): ...
+
+ class EmailService:
+     def send(self, to, subject, body): ...
+
+ class ReportService:
+     def generate(self, report_type, params): ...
+
+ class PaymentService:
+     def process(self, amount, method): ...
```

### 4. Long Parameter List

```diff
# BAD: Too many parameters
- def create_user(email, password, name, age, address, city, country, phone):
-     ...

# GOOD: Group related parameters
+ from dataclasses import dataclass
+
+ @dataclass
+ class UserData:
+     email: str
+     password: str
+     name: str
+     age: int | None = None
+     address: str | None = None
+     phone: str | None = None
+
+ def create_user(data: UserData) -> None:
+     ...
```

### 5. Feature Envy

```diff
# BAD: Method that uses another object's data more than its own
- class Order:
-     def calculate_discount(self, user):
-         if user.membership_level == "gold":
-             return self.total * 0.2
-         if user.account_age > 365:
-             return self.total * 0.1
-         return 0

# GOOD: Move logic to the object that owns the data
+ class User:
+     def get_discount_rate(self) -> float:
+         if self.membership_level == "gold":
+             return 0.2
+         if self.account_age > 365:
+             return 0.1
+         return 0.0
+
+ class Order:
+     def calculate_discount(self, user: User) -> float:
+         return self.total * user.get_discount_rate()
```

### 6. Primitive Obsession

```diff
# BAD: Using primitives for domain concepts
- def send_email(to, subject, body): ...
- send_email("user@example.com", "Hello", "...")
-
- def create_phone(country, number):
-     return f"{country}-{number}"

# GOOD: Use domain types
+ import re
+ from dataclasses import dataclass
+
+ @dataclass(frozen=True)
+ class Email:
+     value: str
+
+     def __post_init__(self) -> None:
+         if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", self.value):
+             raise ValueError(f"Invalid email: {self.value}")
+
+ @dataclass(frozen=True)
+ class PhoneNumber:
+     country: str
+     number: str
+
+     def __post_init__(self) -> None:
+         if not self.country or not self.number:
+             raise ValueError("Invalid phone number")
+
+     def __str__(self) -> str:
+         return f"{self.country}-{self.number}"
+
+ # Usage
+ email = Email("user@example.com")
+ phone = PhoneNumber("1", "555-1234")
```

### 7. Magic Numbers/Strings

```diff
# BAD: Unexplained values
- if user.status == 2: ...
- discount = total * 0.15
- time.sleep(86400)

# GOOD: Named constants
+ from enum import IntEnum, StrEnum
+
+ class UserStatus(IntEnum):
+     ACTIVE = 1
+     INACTIVE = 2
+     SUSPENDED = 3
+
+ class DiscountRate(float, StrEnum):
+     STANDARD = "0.1"
+     PREMIUM = "0.15"
+     VIP = "0.2"
+
+ ONE_DAY_SECONDS: int = 24 * 60 * 60
+
+ if user.status == UserStatus.INACTIVE: ...
+ discount = total * float(DiscountRate.PREMIUM)
+ time.sleep(ONE_DAY_SECONDS)
```

### 8. Nested Conditionals

```diff
# BAD: Arrow code
- def process(order):
-     if order:
-         if order.user:
-             if order.user.is_active:
-                 if order.total > 0:
-                     return process_order(order)
-                 else:
-                     return {"error": "Invalid total"}
-             else:
-                 return {"error": "User inactive"}
-         else:
-             return {"error": "No user"}
-     else:
-         return {"error": "No order"}

# GOOD: Guard clauses / early returns
+ def process(order):
+     if not order:
+         return {"error": "No order"}
+     if not order.user:
+         return {"error": "No user"}
+     if not order.user.is_active:
+         return {"error": "User inactive"}
+     if order.total <= 0:
+         return {"error": "Invalid total"}
+     return process_order(order)
```

### 9. Dead Code

```diff
# BAD: Unused code lingers
- def old_implementation(): ...
- DEPRECATED_VALUE = 5
- from somewhere import unused_thing
- # Commented out code
- # def old_code(): ...

# GOOD: Remove it
+ # Delete unused functions, imports, and commented code
+ # If you need it again, git history has it
```

### 10. Inappropriate Intimacy

```diff
# BAD: One class reaches deep into another
- class OrderProcessor:
-     def process(self, order):
-         order.user.profile.address.street  # Too intimate
-         order.repository.connection.config  # Breaking encapsulation

# GOOD: Ask, don't tell
+ class OrderProcessor:
+     def process(self, order) -> None:
+         order.get_shipping_address()  # Order knows how to get it
+         order.save()  # Order knows how to save itself
```

---

## Extract Method Refactoring

### Before and After

```diff
# Before: One long function
- def print_report(users):
-     print("USER REPORT")
-     print("===========")
-     print("")
-     print(f"Total users: {len(users)}")
-     print("")
-     print("ACTIVE USERS")
-     print("------------")
-     active = [u for u in users if u.is_active]
-     for u in active:
-         print(f"- {u.name} ({u.email})")
-     print("")
-     print(f"Active: {len(active)}")
-     print("")
-     print("INACTIVE USERS")
-     print("--------------")
-     inactive = [u for u in users if not u.is_active]
-     for u in inactive:
-         print(f"- {u.name} ({u.email})")
-     print("")
-     print(f"Inactive: {len(inactive)}")

# After: Extracted methods
+ def print_report(users: list) -> None:
+     _print_header("USER REPORT")
+     print(f"Total users: {len(users)}\n")
+     _print_user_section("ACTIVE USERS", [u for u in users if u.is_active])
+     _print_user_section("INACTIVE USERS", [u for u in users if not u.is_active])
+
+ def _print_header(title: str) -> None:
+     print(title)
+     print("=" * len(title))
+     print("")
+
+ def _print_user_section(title: str, users: list) -> None:
+     print(title)
+     print("-" * len(title))
+     for u in users:
+         print(f"- {u.name} ({u.email})")
+     print("")
+     print(f"{title.split()[0]}: {len(users)}")
+     print("")
```

---

## Introducing Type Safety

### From Untyped to Typed

```diff
# Before: No types
- def calculate_discount(user, total, membership, date):
-     if membership == "gold" and date.weekday() == 4:  # Friday
-         return total * 0.25
-     if membership == "gold":
-         return total * 0.2
-     return total * 0.1

# After: Full type safety
+ from dataclasses import dataclass
+ from datetime import date as Date
+ from enum import StrEnum
+
+ class Membership(StrEnum):
+     BRONZE = "bronze"
+     SILVER = "silver"
+     GOLD = "gold"
+
+ @dataclass
+ class User:
+     id: str
+     name: str
+     membership: Membership
+
+ @dataclass
+ class DiscountResult:
+     original: float
+     discount: float
+     final: float
+     rate: float
+
+ def calculate_discount(
+     user: User,
+     total: float,
+     today: Date | None = None,
+ ) -> DiscountResult:
+     if total < 0:
+         raise ValueError("Total cannot be negative")
+
+     if today is None:
+         today = Date.today()
+
+     rate = 0.1  # Default bronze
+
+     if user.membership == Membership.GOLD and today.weekday() == 4:  # Friday
+         rate = 0.25  # Friday bonus for gold
+     elif user.membership == Membership.GOLD:
+         rate = 0.2
+     elif user.membership == Membership.SILVER:
+         rate = 0.15
+
+     discount = total * rate
+     return DiscountResult(original=total, discount=discount, final=total - discount, rate=rate)
```

---

## Design Patterns for Refactoring

### Strategy Pattern

```diff
# Before: Conditional logic
- def calculate_shipping(order, method: str) -> float:
-     if method == "standard":
-         return 0.0 if order.total > 50 else 5.99
-     elif method == "express":
-         return 9.99 if order.total > 100 else 14.99
-     elif method == "overnight":
-         return 29.99

# After: Strategy pattern
+ from abc import ABC, abstractmethod
+
+ class ShippingStrategy(ABC):
+     @abstractmethod
+     def calculate(self, order) -> float: ...
+
+ class StandardShipping(ShippingStrategy):
+     def calculate(self, order) -> float:
+         return 0.0 if order.total > 50 else 5.99
+
+ class ExpressShipping(ShippingStrategy):
+     def calculate(self, order) -> float:
+         return 9.99 if order.total > 100 else 14.99
+
+ class OvernightShipping(ShippingStrategy):
+     def calculate(self, order) -> float:
+         return 29.99
+
+ def calculate_shipping(order, strategy: ShippingStrategy) -> float:
+     return strategy.calculate(order)
```

### Chain of Responsibility

```diff
# Before: Nested validation
- def validate(user) -> list[str]:
-     errors = []
-     if not user.email:
-         errors.append("Email required")
-     elif not is_valid_email(user.email):
-         errors.append("Invalid email")
-     if not user.name:
-         errors.append("Name required")
-     if user.age < 18:
-         errors.append("Must be 18+")
-     if user.country == "blocked":
-         errors.append("Country not supported")
-     return errors

# After: Chain of responsibility
+ from abc import ABC, abstractmethod
+
+ class Validator(ABC):
+     def __init__(self) -> None:
+         self._next: Validator | None = None
+
+     def set_next(self, validator: "Validator") -> "Validator":
+         self._next = validator
+         return validator
+
+     def validate(self, user) -> str | None:
+         error = self._do_validate(user)
+         if error:
+             return error
+         return self._next.validate(user) if self._next else None
+
+     @abstractmethod
+     def _do_validate(self, user) -> str | None: ...
+
+ class EmailRequiredValidator(Validator):
+     def _do_validate(self, user) -> str | None:
+         return "Email required" if not user.email else None
+
+ class EmailFormatValidator(Validator):
+     def _do_validate(self, user) -> str | None:
+         if user.email and not is_valid_email(user.email):
+             return "Invalid email"
+         return None
+
+ # Build the chain
+ validator = EmailRequiredValidator()
+ (validator
+     .set_next(EmailFormatValidator())
+     .set_next(NameRequiredValidator())
+     .set_next(AgeValidator())
+     .set_next(CountryValidator()))
```

---

## Refactoring Steps

### Safe Refactoring Process

```
1. PREPARE
   - Ensure tests exist (write them if missing)
   - Commit current state
   - Create feature branch

2. IDENTIFY
   - Find the code smell to address
   - Understand what the code does
   - Plan the refactoring

3. REFACTOR (small steps)
   - Make one small change
   - Run tests
   - Commit if tests pass
   - Repeat

4. VERIFY
   - All tests pass
   - Manual testing if needed
   - Performance unchanged or improved

5. CLEAN UP
   - Update comments
   - Update documentation
   - Final commit
```

---

## Refactoring Checklist

### Code Quality

- [ ] Functions are small (< 50 lines)
- [ ] Functions do one thing
- [ ] No duplicated code
- [ ] Descriptive names (variables, functions, classes)
- [ ] No magic numbers/strings
- [ ] Dead code removed

### Structure

- [ ] Related code is together
- [ ] Clear module boundaries
- [ ] Dependencies flow in one direction
- [ ] No circular dependencies

### Type Safety

- [ ] Types defined for all public APIs
- [ ] No `any` types without justification
- [ ] Nullable types explicitly marked

### Testing

- [ ] Refactored code is tested
- [ ] Tests cover edge cases
- [ ] All tests pass

---

## Common Refactoring Operations

| Operation                                     | Description                           |
| --------------------------------------------- | ------------------------------------- |
| Extract Method                                | Turn code fragment into method        |
| Extract Class                                 | Move behavior to new class            |
| Extract Interface                             | Create interface from implementation  |
| Inline Method                                 | Move method body back to caller       |
| Inline Class                                  | Move class behavior to caller         |
| Pull Up Method                                | Move method to superclass             |
| Push Down Method                              | Move method to subclass               |
| Rename Method/Variable                        | Improve clarity                       |
| Introduce Parameter Object                    | Group related parameters              |
| Replace Conditional with Polymorphism         | Use polymorphism instead of switch/if |
| Replace Magic Number with Constant            | Named constants                       |
| Decompose Conditional                         | Break complex conditions              |
| Consolidate Conditional                       | Combine duplicate conditions          |
| Replace Nested Conditional with Guard Clauses | Early returns                         |
| Introduce Null Object                         | Eliminate null checks                 |
| Replace Type Code with Class/Enum             | Strong typing                         |
| Replace Inheritance with Delegation           | Composition over inheritance          |
