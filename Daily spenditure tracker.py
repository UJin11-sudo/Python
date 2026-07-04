#Take Input from user -> store in a list -> sum all the expenses -> display total expenditure

expenses = []
while True:
    expense = input("Enter an expense (or 'done' to finish): ")
    if expense == "done":
        break
    expenses.append(float(expense))

total_expenditure = sum(expenses)
print(f"Total expenditure: ₹{total_expenditure:.2f}")