from typing import Dict, Any, Optional
from app.agent.intent import intent_classifier
from app.agent.entities import entity_extractor
from app.agent.tools import tools
from app.models.evidence import Evidence
from app.agent.session import session_manager
from app.agent.groq_service import groq_service
from app.agent.validator import validator


class RoadSenseAgent:
    def __init__(self):
        self.classifier = intent_classifier
        self.extractor = entity_extractor
        self.tools = tools

    def process_request(
        self,
        question: str,
        session_id: str = "default",
        survey_id: Optional[str] = None
    ) -> Dict[str, Any]:

        session = session_manager.get_session(session_id)
        intent_data = self.classifier.predict(question)
        intent = intent_data["intent"]
        confidence = intent_data["confidence"]
        entities = self.extractor.extract_entities(question)

        data = {}
        evidence_objs = []
        answer = "I'm analyzing the active survey dataset..."

        # -----------------------------------------------------
        # INTENT 1: Critical / High Priority Query
        # -----------------------------------------------------
        if intent == "priority_query" or "critical" in question.lower() or "priority" in question.lower():
            critical_items = self.tools.get_critical_damages(survey_id)
            stats = self.tools.get_survey_statistics(survey_id)
            data = {"critical_damages": critical_items, "summary": stats}
            
            evidence_objs.append(
                Evidence(
                    tool="get_critical_damages",
                    verified_facts={
                        "critical_count": len(critical_items),
                        "total_damages": stats["total_damages"],
                        "critical_damages": critical_items
                    }
                )
            )

            if critical_items:
                crit_codes = ", ".join([d["damage_code"] for d in critical_items[:5]])
                answer = (
                    f"Based on the verified database records for this survey, there are "
                    f"**{len(critical_items)} Critical/Priority-1 defect(s)** ({crit_codes}). "
                    f"These require immediate crew dispatch and traffic safety mitigation."
                )
            else:
                answer = (
                    f"There are currently **0 Critical (Priority 1)** defects detected in this survey. "
                    f"Total road defects logged: {stats['total_damages']}."
                )

        # -----------------------------------------------------
        # INTENT 2: Cost & Budget Query
        # -----------------------------------------------------
        elif intent == "cost_query" or "cost" in question.lower() or "budget" in question.lower():
            stats = self.tools.get_survey_statistics(survey_id)
            data = stats
            evidence_objs.append(
                Evidence(
                    tool="get_survey_statistics",
                    verified_facts={
                        "total_estimated_cost": stats["total_estimated_cost"],
                        "total_damages": stats["total_damages"]
                    }
                )
            )
            answer = (
                f"The total estimated repair budget for this surveyed corridor is "
                f"**Rs {stats['total_estimated_cost']:,.2f}** across {stats['total_damages']} identified distress instances."
            )

        # -----------------------------------------------------
        # INTENT 3: Specific Defect Detail Query
        # -----------------------------------------------------
        elif intent == "damage_query" or entities.get("damage_id"):
            d_code = entities.get("damage_id", "")
            if not d_code:
                # Check for DMG- pattern in question
                import re
                m = re.search(r"(DMG-[A-Za-z0-9\-]+)", question, re.I)
                if m:
                    d_code = m.group(1)

            if d_code:
                dmg = self.tools.get_damage_by_code(d_code, survey_id)
                data = dmg
                if "error" in dmg:
                    answer = f"Defect {d_code} could not be found in the current survey."
                else:
                    evidence_objs.append(
                        Evidence(
                            tool="get_damage_by_code",
                            damage_ids=[d_code],
                            verified_facts=dmg
                        )
                    )
                    gps_text = f"Lat: {dmg['latitude']}, Lon: {dmg['longitude']}" if dmg.get("gps_available") else "GPS Unavailable (Frame-indexed)"
                    answer = (
                        f"**Defect {dmg['damage_code']} Details:**\n"
                        f"- Type: **{dmg['damage_type'].capitalize()}**\n"
                        f"- Severity: **{dmg['severity']}** (Priority {dmg['priority']})\n"
                        f"- Model Confidence: **{dmg['confidence']:.2f}**\n"
                        f"- RCI Score: **{dmg['rci']:.1f} / 100**\n"
                        f"- Est. Repair Cost: **Rs {dmg['estimated_repair_cost']:,.2f}**\n"
                        f"- Positional Ref: {gps_text}\n"
                        f"- Verification Status: {dmg['verification_status']}"
                    )
            else:
                answer = "Please specify the defect code (e.g., DMG-001) to inspect its engineering profile."

        # -----------------------------------------------------
        # INTENT 4: Crew & Dispatch Query
        # -----------------------------------------------------
        elif "crew" in question.lower() or "dispatch" in question.lower():
            crews = self.tools.get_crew_workloads()
            data = {"crews": crews}
            evidence_objs.append(
                Evidence(
                    tool="get_crew_workloads",
                    verified_facts={"crews": crews}
                )
            )
            crew_lines = "\n".join([
                f"- **{c['crew_name']}** ({c['crew_code']}): Status {c['status']}, Capacity {c['capacity_tons']} Tons, Tasks Assigned: {c['assigned_tasks']}/{c['max_daily_jobs']}"
                for c in crews
            ])
            answer = f"**Municipal Maintenance Crew Deployment Status:**\n{crew_lines}"

        # -----------------------------------------------------
        # INTENT 5: Survey Summary / General Query
        # -----------------------------------------------------
        else:
            stats = self.tools.get_survey_statistics(survey_id)
            data = stats
            evidence_objs.append(
                Evidence(
                    tool="get_survey_statistics",
                    verified_facts=stats
                )
            )
            by_type_str = ", ".join([f"{count} {t}" for t, count in stats["by_type"].items()]) if stats["by_type"] else "No defects"
            answer = (
                f"**Survey Overview:**\n"
                f"- Total Recorded Distresses: **{stats['total_damages']}**\n"
                f"- Breakdown: {by_type_str}\n"
                f"- Severity: Critical: {stats['critical_count']}, High: {stats['high_count']}\n"
                f"- Average RCI: **{stats['avg_rci']:.1f} / 100**\n"
                f"- Total Estimated Repair Cost: **Rs {stats['total_estimated_cost']:,.2f}**"
            )

        evidence_dicts = [e.model_dump() for e in evidence_objs]

        # Optional Groq LLM refinement with strict numerical validation
        final_answer = answer
        if evidence_dicts and groq_service:
            try:
                groq_resp = groq_service.generate_explanation(
                    question, intent, entities, evidence_dicts, answer
                )
                if groq_resp and validator.validate_numbers(groq_resp, evidence_dicts):
                    final_answer = groq_resp
            except Exception:
                pass

        session_manager.update_session(session_id, {
            "previous_intent": intent,
            "previous_result": data,
            "last_evidence": evidence_dicts
        })

        return {
            "answer": final_answer,
            "intent": intent,
            "confidence": confidence,
            "evidence": evidence_dicts,
            "data": data
        }


agent = RoadSenseAgent()
