from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ActionItem:
    action: str
    status: str
    reason: str
    used_data: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)


@dataclass
class ActionPlan:
    use_case_id: str
    title: str
    user_request: str
    tasks: List[str] = field(default_factory=list)
    involved_agents: List[str] = field(default_factory=list)
    actions: List[ActionItem] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    def add_task(self, task: str) -> None:
        self.tasks.append(task)

    def add_agent(self, agent: str) -> None:
        if agent not in self.involved_agents:
            self.involved_agents.append(agent)

    def add_action(
        self,
        action: str,
        status: str,
        reason: str,
        used_data: List[str] | None = None,
        uncertainties: List[str] | None = None,
    ) -> None:
        allowed_status = {"erlaubt", "freigabepflichtig", "blockiert"}

        if status not in allowed_status:
            raise ValueError(f"Ungültiger Status: {status}")

        self.actions.append(
            ActionItem(
                action=action,
                status=status,
                reason=reason,
                used_data=used_data or [],
                uncertainties=uncertainties or [],
            )
        )

    def add_open_question(self, question: str) -> None:
        self.open_questions.append(question)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "use_case_id": self.use_case_id,
            "title": self.title,
            "user_request": self.user_request,
            "tasks": self.tasks,
            "involved_agents": self.involved_agents,
            "actions": [
                {
                    "action": item.action,
                    "status": item.status,
                    "reason": item.reason,
                    "used_data": item.used_data,
                    "uncertainties": item.uncertainties,
                }
                for item in self.actions
            ],
            "open_questions": self.open_questions,
        }

    def print_summary(self) -> None:
        print("=" * 80)
        print(f"Use Case: {self.title}")
        print("=" * 80)

        print("\nNutzeranfrage:")
        print(self.user_request)

        print("\nErkannte Teilaufgaben:")
        for index, task in enumerate(self.tasks, start=1):
            print(f"{index}. {task}")

        print("\nBeteiligte Agenten:")
        for agent in self.involved_agents:
            print(f"- {agent}")

        print("\nVorgeschlagene Aktionen:")
        for index, item in enumerate(self.actions, start=1):
            print(f"\n{index}. {item.action}")
            print(f"   Status: {item.status}")
            print(f"   Begründung: {item.reason}")

            if item.used_data:
                print(f"   Verwendete Daten: {', '.join(item.used_data)}")

            if item.uncertainties:
                print(f"   Unsicherheiten: {', '.join(item.uncertainties)}")

        if self.open_questions:
            print("\nOffene Rückfragen:")
            for question in self.open_questions:
                print(f"- {question}")


if __name__ == "__main__":
    plan = ActionPlan(
        use_case_id="test",
        title="Test ActionPlan",
        user_request="Teste die ActionPlan-Ausgabe.",
    )

    plan.add_task("Anfrage analysieren")
    plan.add_agent("Orchestrator Agent")
    plan.add_action(
        action="Fehlendes Modul markieren",
        status="erlaubt",
        reason="Das Markieren fehlender Inhalte ist eine vorbereitende Aktion.",
        used_data=["Module", "ContentItem"],
    )
    plan.add_action(
        action="Lernende automatisch einschreiben",
        status="freigabepflichtig",
        reason="Die Einschreibung hat organisatorische Auswirkungen.",
        used_data=["User", "Group", "PermissionRule"],
    )
    plan.add_action(
        action="Personenbezogene Testergebnisse an Teamleiter senden",
        status="blockiert",
        reason="Teamleiter dürfen keine personenbezogenen Leistungsdaten ohne Freigabe erhalten.",
        used_data=["TestResult", "PermissionRule"],
        uncertainties=["Berechtigung für personenbezogenes Reporting unklar"],
    )

    plan.print_summary()