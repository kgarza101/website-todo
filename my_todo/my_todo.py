import reflex as rx
from typing import Optional
from sqlmodel import select
from .models import User, Task

class Task(rx.Base):
    name: str
    date: str
    notes: str
    status: str
    assigned_to: str
    group: str  # Add group field to associate tasks with groups

# Sample tasks for demo purposes
INITIAL_TASKS = {
    "team1": [
        Task(name="Team1 Task", date="2023-07-01", notes="Sample task for team1", 
             status="Not Started", assigned_to="member1", group="team1")
    ],
    "team2": [
        Task(name="Team2 Task", date="2023-07-02", notes="Sample task for team2", 
             status="In Progress", assigned_to="member2", group="team2")
    ],
    "admin": []
}

import reflex as rx
from typing import Optional
from .models import User, Task

class State(rx.State):
    """The app state."""
    
    # Auth state
    is_authenticated: bool = False
    current_user: Optional[User] = None
    error_message: str = ""
    
    # View state
    show_signup: bool = False
    signup_error: str = ""
    
    # Modal state
    show_role_modal: bool = False
    role_password: str = ""
    role_modal_error: str = ""
    selected_role: str = ""
    
    # Edit modal state
    show_edit_modal: bool = False
    editing_task: Optional[Task] = None
    edit_name: str = ""
    edit_date: str = ""
    edit_notes: str = ""
    edit_status: str = ""
    edit_assigned_to: str = ""

    def set_edit_name(self, name: str):
        """Set the edit name field."""
        self.edit_name = name

    def set_edit_date(self, date: str):
        """Set the edit date field."""
        self.edit_date = date

    def set_edit_notes(self, notes: str):
        """Set the edit notes field."""
        self.edit_notes = notes

    def set_edit_status(self, status: str):
        """Set the edit status field."""
        self.edit_status = status

    def set_edit_assigned_to(self, assigned_to: str):
        """Set the edit assigned_to field."""
        self.edit_assigned_to = assigned_to

    def show_login_form(self):
        """Switch to login view."""
        self.show_signup = False
        self.signup_error = ""
        self.error_message = ""
    
    def show_signup_form(self):
        """Switch to signup view."""
        self.show_signup = True
        self.error_message = ""
        self.signup_error = ""
        
    def open_edit_modal(self, task: Task):
        """Open the edit modal for a task."""
        self.editing_task = task
        self.edit_name = task.name
        self.edit_date = task.date
        self.edit_notes = task.notes
        self.edit_status = task.status
        self.edit_assigned_to = task.assigned_to
        self.show_edit_modal = True

    def close_edit_modal(self):
        """Close the edit modal."""
        self.show_edit_modal = False
        self.editing_task = None
        self.edit_name = ""
        self.edit_date = ""
        self.edit_notes = ""
        self.edit_status = ""
        self.edit_assigned_to = ""

    def logout(self):
        """Handle user logout."""
        self.is_authenticated = False
        self.current_user = None
        self.error_message = ""

    def set_role(self, role: str):
        """Handle role change."""
        if not self.current_user:
            return
            
        # Only show modal for Manager role if not already a Manager
        if role == "Manager" and self.current_user.role != "Manager":
            self.selected_role = role
            self.show_role_modal = True
        else:
            # Directly switch to Assignee role or if already a Manager
            try:
                with rx.session() as session:
                    user = session.exec(select(User).where(User.id == self.current_user.id)).first()
                    if user:
                        user.role = role
                        session.add(user)
                        session.commit()
                        # Create a new user object to trigger state update
                        self.current_user = User(
                            id=user.id,
                            username=user.username,
                            password=user.password,
                            role=role,
                            manager_password=user.manager_password
                        )
            except Exception as e:
                print(f"Error switching role: {str(e)}")
    
    def verify_role_password(self):
        """Verify the password for role switching."""
        if not self.current_user:
            return
            
        try:
            with rx.session() as session:
                user = session.exec(select(User).where(User.id == self.current_user.id)).first()
                if not user:
                    return
                    
                if self.role_password == user.manager_password:
                    user.role = self.selected_role
                    session.add(user)
                    session.commit()
                    # Create a new user object to trigger state update
                    self.current_user = User(
                        id=user.id,
                        username=user.username,
                        password=user.password,
                        role=self.selected_role,
                        manager_password=user.manager_password
                    )
                    self.close_role_modal()
                else:
                    self.role_modal_error = "Invalid password for Manager role."
        except Exception as e:
            print(f"Error verifying role password: {str(e)}")
            self.role_modal_error = "Error verifying password. Please try again."
    
    def close_role_modal(self):
        """Close the role switch modal."""
        self.show_role_modal = False
        self.role_password = ""
        self.role_modal_error = ""
        
    def set_role_password(self, password: str):
        """Update the role password field."""
        self.role_password = password

    def add_item(self, form_data: dict):
        """Add a new task."""
        if not self.current_user or self.current_user.role != "Manager":
            return
            
        try:
            with rx.session() as session:
                new_task = Task(
                    name=form_data.get("name", ""),
                    date=form_data.get("date", ""),
                    notes=form_data.get("notes", ""),
                    status=form_data.get("status", "Not Started"),
                    assigned_to=form_data.get("assigned_to", ""),
                    owner_id=self.current_user.id
                )
                session.add(new_task)
                session.commit()
                # Force state update by refreshing current_user
                self.current_user = session.exec(select(User).where(User.id == self.current_user.id)).first()
        except Exception as e:
            print(f"Error adding task: {str(e)}")

    @rx.var
    def current_tasks(self) -> list[Task]:
        """Return tasks for the current user."""
        if not self.current_user:
            return []
        try:
            with rx.session() as session:
                tasks = session.exec(select(Task).where(Task.owner_id == self.current_user.id)).all()
                return tasks
        except Exception as e:
            print(f"Error getting tasks: {str(e)}")
            return []

    def login(self, form_data: dict):
        """Handle user login."""
        username = form_data.get("username", "")
        password = form_data.get("password", "")
        
        if not username or not password:
            self.error_message = "Please enter both username and password."
            return
        
        try:
            with rx.session() as session:
                user = session.exec(select(User).where(User.username == username)).first()
                if user and user.password == password:
                    self.is_authenticated = True
                    user.role = "Assignee"
                    self.current_user = user
                    self.error_message = ""
                else:
                    self.error_message = "Invalid username or password."
        except Exception as e:
            self.error_message = "Error during login. Please try again."
            print(f"Login error: {str(e)}")  # For debugging

    def signup(self, form_data: dict):
        """Handle new user signup."""
        username = form_data.get("username", "")
        password = form_data.get("password", "")
        confirm_password = form_data.get("confirm_password", "")
        manager_password = form_data.get("manager_password", "")
        
        if not all([username, password, confirm_password, manager_password]):
            self.signup_error = "All fields are required."
            return
            
        if password != confirm_password:
            self.signup_error = "Passwords do not match."
            return
            
        try:
            with rx.session() as session:
                if session.exec(select(User).where(User.username == username)).first():
                    self.signup_error = "Username already exists."
                    return
                    
                new_user = User(
                    username=username,
                    password=password,  # In production, use hashed passwords
                    role="Manager",  # First user is the manager
                    manager_password=manager_password
                )
                session.add(new_user)
                session.commit()
                
                # Refresh the user to get the ID
                session.refresh(new_user)
                
                # Auto login after signup
                self.is_authenticated = True
                self.current_user = new_user
                self.signup_error = ""
                self.show_signup = False
        except Exception as e:
            self.signup_error = "Error creating user. Please try again."
            print(f"Signup error: {str(e)}")  # For debugging

    def edit_item(self, form_data: dict):
        """Handle task editing."""
        if not self.editing_task or not self.current_user:
            return
            
        try:
            with rx.session() as session:
                task = session.exec(select(Task).where(Task.id == self.editing_task.id)).first()
                if task:
                    if self.current_user.role == "Manager":
                        # Managers can edit all fields
                        task.name = self.edit_name
                        task.date = self.edit_date
                        task.notes = self.edit_notes
                        task.status = self.edit_status
                        task.assigned_to = self.edit_assigned_to
                    else:
                        # Assignees can only edit status
                        task.status = self.edit_status
                    session.add(task)
                    session.commit()
                    # Force state update by refreshing current_user
                    self.current_user = session.exec(select(User).where(User.id == self.current_user.id)).first()
            self.close_edit_modal()
        except Exception as e:
            print(f"Error editing task: {str(e)}")

    def delete_item(self, task_id: int):
        """Delete a task."""
        if not self.current_user or self.current_user.role != "Manager":
            return
            
        try:
            with rx.session() as session:
                task = session.exec(select(Task).where(Task.id == task_id)).first()
                if task:
                    session.delete(task)
                    session.commit()
                    # Force state update by refreshing current_user
                    self.current_user = session.exec(select(User).where(User.id == self.current_user.id)).first()
        except Exception as e:
            print(f"Error deleting task: {str(e)}")

def create_initial_data():
    """Initialize the database with sample data."""
    with rx.session() as session:
        # Check if test user exists
        test_user = session.exec(select(User).where(User.username == "testuser")).first()
        if not test_user:
            # Create test user
            test_user = User(
                username="testuser",
                password="test123",  # In production, use hashed passwords
                manager_password="manager123"
            )
            session.add(test_user)
            session.commit()

            # Add some sample tasks
            task1 = Task(
                name="Complete Project",
                date="2024-03-20",
                notes="Finish the todo app project",
                status="In Progress",
                assigned_to="testuser",
                owner_id=test_user.id
            )
            task2 = Task(
                name="Test Database",
                date="2024-03-21",
                notes="Test all database operations",
                status="Not Started",
                assigned_to="testuser",
                owner_id=test_user.id
            )
            session.add(task1)
            session.add(task2)
            session.commit()

        # Check if test assignee exists
        test_assignee = session.exec(select(User).where(User.username == "assignee")).first()
        if not test_assignee:
            # Create test assignee
            test_assignee = User(
                username="assignee",
                password="assignee123",
                manager_password=""
            )
            session.add(test_assignee)
            session.commit()

def _badge(icon: str, text: str, color_scheme: str):
    return rx.badge(
        rx.icon(icon, size=16),
        text,
        color_scheme=color_scheme,
        radius="full",
        variant="soft",
        size="3",
    )

def status_badge(status: str):
    badge_mapping = {
        "Completed": ("check", "Completed", "green"),
        "In Progress": ("loader", "In Progress", "yellow"),
        "Not Started": ("ban", "Not Started", "red"),
    }
    return _badge(*badge_mapping.get(status, ("loader", "In progress", "yellow")))

def role_switcher():
    return rx.cond(
        State.current_user != None,
        rx.select(
            ["Manager", "Assignee"],
            placeholder="Switch Role",
            value=rx.cond(
                State.current_user != None,
                State.current_user.role,
                "Assignee"
            ),
            on_change=State.set_role,
        ),
        rx.box(),  # Empty box when no user is logged in
    )

def role_modal():
    return rx.cond(
        State.show_role_modal,
        rx.box(
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading("Manager Role Authentication", size="5"),
                        rx.divider(),
                        rx.text("Manager role requires password verification."),
                        rx.cond(
                            State.role_modal_error != "",
                            rx.text(State.role_modal_error, color="red", margin_bottom="1em")
                        ),
                        rx.input(
                            placeholder="Enter manager password",
                            type="password",
                            on_change=State.set_role_password,
                            value=State.role_password,
                            width="100%",
                            margin_bottom="1em",
                        ),
                        rx.hstack(
                            rx.button(
                                "Cancel",
                                on_click=State.close_role_modal,
                                color_scheme="gray",
                            ),
                            rx.button(
                                "Verify",
                                on_click=State.verify_role_password,
                                color_scheme="green",
                            ),
                            justify="end",
                            width="100%",
                        ),
                        spacing="4",
                    ),
                    width="400px",
                ),
                justify="center",
                align="center",
                height="100%",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100%",
            height="100vh",
            backdrop_filter="blur(2px)",
            bg="rgba(0, 0, 0, 0.5)",
            z_index="1000",
        ),
        rx.box(),
    )

def show_item(task: Task):
    return rx.table.row(
        rx.table.cell(task.name),
        rx.table.cell(task.date),
        rx.table.cell(task.notes),
        rx.table.cell(
            rx.match(
                task.status,
                ("Completed", status_badge("Completed")),
                ("In Progress", status_badge("In Progress")),
                ("Not Started", status_badge("Not Started")),
                status_badge("Not Started"),
            )
        ),
        rx.table.cell(task.assigned_to),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "Edit",
                    color_scheme="blue",
                    size="2",
                    on_click=lambda: State.open_edit_modal(task),
                ),
                rx.cond(
                    (State.current_user != None) & (State.current_user.role == "Manager"),
            rx.button(
                "Delete",
                color_scheme="red",
                size="2",
                        on_click=lambda: State.delete_item(task.id),
                    ),
                ),
                spacing="2",
            )
        ),
    )

def add_item_form():
    return rx.form(
        rx.hstack(
            rx.input(placeholder="Task", name="name", required=True),
            rx.input(type="date", name="date", required=True),
            rx.input(placeholder="Notes", name="notes"),
            rx.select(
                ["Completed", "In Progress", "Not Started"],
                name="status",
                placeholder="Status",
                required=True,
            ),
            rx.input(placeholder="Assigned To", name="assigned_to", required=True),  # NEW
            rx.button("Add", type="submit", color_scheme="green", size="2"),
        ),
        on_submit=State.add_item,
        reset_on_submit=True,
        padding_x = "2em",
    )

def signup_form():
    return rx.center(
        rx.vstack(
            rx.heading("Create New Group", size="6", margin_bottom="1em"),
            rx.cond(
                State.signup_error != "",
                rx.text(State.signup_error, color="red", margin_bottom="1em")
            ),
            rx.form(
                rx.vstack(
                    rx.input(
                        placeholder="Group Username",
                        name="username",
                        required=True,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Group Password",
                        name="password",
                        type="password",
                        required=True,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Confirm Password",
                        name="confirm_password",
                        type="password",
                        required=True,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Manager Password",
                        name="manager_password",
                        type="password",
                        required=True,
                        width="100%",
                    ),
                    rx.button(
                        "Sign Up",
                        type="submit",
                        color_scheme="blue",
                        size="3",
                        width="100%",
                    ),
                    rx.button(
                        "Back to Login",
                        color_scheme="gray",
                        size="3",
                        width="100%",
                        on_click=State.show_login_form,
                    ),
                    spacing="4",
                    width="300px",
                ),
                on_submit=State.signup,
            ),
            width="400px",
            padding="2em",
            border_radius="lg",
            background="white",
            box_shadow="lg",
        ),
        width="100%",
        height="100vh",
    )

def login_form():
    return rx.center(
        rx.vstack(
            rx.heading("Task Management Login", size="6", margin_bottom="1em"),
            rx.cond(
                State.error_message != "",
                rx.text(State.error_message, color="red", margin_bottom="1em")
            ),
            rx.form(
                rx.vstack(
                    rx.input(
                        placeholder="Group Username",
                        name="username",
                        required=True,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Group Password",
                        name="password",
                        type="password",
                        required=True,
                        width="100%",
                    ),
                    rx.button(
                        "Login",
                        type="submit",
                        color_scheme="green",
                        size="3",
                        width="100%",
                    ),
                    rx.text("or", align_self="center"),
                    rx.button(
                        "Create New Group",
                        color_scheme="blue",
                        size="3",
                        width="100%",
                        on_click=State.show_signup_form,
                    ),
                    spacing="4",
                    width="300px",
                ),
                on_submit=State.login,
            ),
            width="400px",
            padding="2em",
            border_radius="lg",
            background="white",
            box_shadow="lg",
        ),
        width="100%",
        height="100vh",
    )

def navbar():
    return rx.flex(
        rx.badge(
            rx.icon(tag="list-todo", size=28),
            rx.cond(
                State.current_user,
                rx.heading(f"Welcome to {State.current_user.username}'s To-Do List", size="6"),
                rx.heading("Welcome to Guest's To-Do List", size="6"),
            ),
            color_scheme="green",
            radius="large",
            align="center",
            variant="surface",
            padding="0.75rem",
        ),

        role_switcher(),
        rx.spacer(),
        rx.hstack(

            rx.hstack(
            rx.heading("Screen Mode : ", size="2"),
            rx.color_mode.button(),
            spacing="1",  # Keeps label and button close
            align="center",
            ),
            rx.button(
                "Logout",
                color_scheme="red",
                size="2",
                on_click=State.logout,
            ),
            spacing="6",  # More space between color mode group and Logout
            align="center",

        ),
        spacing="2",
        flex_direction=["column", "column", "row"],
        align="center",
        width="100%",
        top="0px",
        padding_top="2em",
        padding_x="2em",
    )

def edit_modal():
    """Modal for editing tasks."""
    return rx.cond(
        State.show_edit_modal,
        rx.box(
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading("Edit Task", size="5"),
                        rx.divider(),
                        rx.form(
                            rx.vstack(
                                rx.cond(
                                    (State.current_user != None) & (State.current_user.role == "Manager"),
                                    rx.vstack(
                                        rx.input(
                                            placeholder="Task",
                                            name="name",
                                            required=True,
                                            value=State.edit_name,
                                            on_change=State.set_edit_name,
                                        ),
                                        rx.input(
                                            type="date",
                                            name="date",
                                            required=True,
                                            value=State.edit_date,
                                            on_change=State.set_edit_date,
                                        ),
                                        rx.input(
                                            placeholder="Notes",
                                            name="notes",
                                            value=State.edit_notes,
                                            on_change=State.set_edit_notes,
                                        ),
                                        rx.input(
                                            placeholder="Assigned To",
                                            name="assigned_to",
                                            required=True,
                                            value=State.edit_assigned_to,
                                            on_change=State.set_edit_assigned_to,
                                        ),
                                    ),
                                    rx.text("Update task status:", margin_bottom="1em"),
                                ),
                                # Status field shown for both roles
                                rx.select(
                                    ["Completed", "In Progress", "Not Started"],
                                    name="status",
                                    placeholder="Status",
                                    required=True,
                                    value=State.edit_status,
                                    on_change=State.set_edit_status,
                                ),
                                rx.hstack(
                                    rx.button(
                                        "Cancel",
                                        on_click=State.close_edit_modal,
                                        color_scheme="gray",
                                    ),
                                    rx.button(
                                        "Save",
                                        type="submit",
                                        color_scheme="green",
                                    ),
                                    justify="end",
                                    width="100%",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            on_submit=State.edit_item,
                        ),
                    ),
                    width="400px",
                ),
                justify="center",
                align="center",
                height="100%",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100%",
            height="100vh",
            backdrop_filter="blur(2px)",
            bg="rgba(0, 0, 0, 0.5)",
            z_index="1000",
        ),
        rx.box(),
    )
    

def dashboard():
    return rx.vstack(
        navbar(),
        rx.cond(
            (State.current_user != None) & (State.current_user.role == "Manager"),
            add_item_form(),
            rx.text("You do not have permission to assign or delete tasks.", color="red", padding_x = "2em"),
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(rx.icon("clipboard-list"),"Task"),
                    rx.table.column_header_cell(rx.icon("calendar-1"),"Date"),
                    rx.table.column_header_cell(rx.icon("notebook-pen"),"Notes"),
                    rx.table.column_header_cell(rx.icon("circle-help"),"Status"),
                    rx.table.column_header_cell(rx.icon("users"),"Assigned To"),
                    rx.table.column_header_cell(rx.icon("cog"),"Actions"),
                ),
            ),
            rx.table.body(
                rx.foreach(State.current_tasks, show_item),
            ),
            width="100%",
        ),
        role_modal(),
        edit_modal(),
    )

def index():
    return rx.cond(
        State.is_authenticated,
        dashboard(),
        rx.cond(
            State.show_signup,
            signup_form(),
            login_form(),
        ),
    )

app = rx.App()
app.add_page(index)
