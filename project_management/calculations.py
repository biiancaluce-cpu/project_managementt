"""Reproducible calculations for phases 2–5 of the coursework.

Expert ratings and task estimates were confirmed by the team. Weekly history
was supplied by the user. Per-task actual time is not available in this file.
"""
from __future__ import annotations

import datetime as dt
import itertools
import json
import math
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent if HERE.name == "work" else HERE
OUT = ROOT / "work" / "all_results.json" if HERE.name == "work" else ROOT / "results.json"
PEOPLE = ["Мартин Майжюс", "Чуев Никита", "Акнур Акмурадова"]

# Phase 2: work needed to prepare the phase 3 estimate, hours and team-confirmed
# private preference scores (1=least preferred, 5=most preferred).
P2 = [
    ("T01", "Границы MVP и роли пользователей", 5, [5, 3, 4]),
    ("T02", "Список и цели Use Cases", 7, [4, 4, 5]),
    ("T03", "Основные и альтернативные потоки UC01–UC06", 8, [3, 4, 5]),
    ("T04", "Основные и альтернативные потоки UC07–UC12", 8, [3, 5, 4]),
    ("T05", "Граница COSMIC и группы данных", 5, [5, 3, 3]),
    ("T06", "Подсчёт движений COSMIC", 9, [5, 4, 2]),
    ("T07", "Акторы и веса UCP", 4, [4, 4, 3]),
    ("T08", "Сложность UC и факторы UCP", 8, [4, 5, 3]),
    ("T09", "Индивидуальные оценки трудоёмкости UC", 6, [3, 3, 5]),
    ("T10", "Агрегация оценок и сравнение методов", 7, [5, 4, 3]),
    ("T11", "Команда, срок и исключения из MVP", 6, [4, 3, 5]),
    ("T12", "Проверка расчётов и оформление фазы 3", 7, [3, 5, 4]),
]

def optimize_assignment(tasks):
    # Exact dynamic program over two workload sums; third follows from total.
    # Objective is total preference points weighted by estimated hours.
    total = sum(t[2] for t in tasks)
    lo, hi = math.floor(total * .25), math.ceil(total * .40)
    states = {(0, 0): (0, ())}
    for _, _, hours, prefs in tasks:
        nxt = {}
        for (a, b), (score, sequence) in states.items():
            for owner in range(3):
                na, nb = a + (hours if owner == 0 else 0), b + (hours if owner == 1 else 0)
                if na > hi or nb > hi:
                    continue
                key = na, nb
                candidate = score + prefs[owner] * hours, sequence + (owner,)
                if key not in nxt or candidate[0] > nxt[key][0]:
                    nxt[key] = candidate
        states = nxt
    feasible = [(v[0], k, v[1]) for k, v in states.items()
                if lo <= k[0] <= hi and lo <= k[1] <= hi and
                lo <= total - k[0] - k[1] <= hi]
    best = max(feasible, key=lambda x: (x[0], -max(x[1][0], x[1][1], total-sum(x[1]))))
    scores, loads, sequence = best
    actual_loads = [sum(t[2] for t, owner in zip(tasks, sequence) if owner == p) for p in range(3)]
    return {"total_hours": total, "bounds_hours": [lo, hi], "objective": scores,
            "loads": actual_loads, "owners": list(sequence),
            "tasks": [{"id": t[0], "name": t[1], "hours": t[2], "preferences": t[3],
                       "owner": PEOPLE[o]} for t, o in zip(tasks, sequence)]}

# Phase 3: one functional process per UC, boundary = booking service. Each
# E/X/R/W is a movement of a distinct data group across that boundary.
UC = [
    ("UC01", "Войти через учётную запись вуза", "Студент/сотрудник", 3, (1,1,1,0), 18,
     "Пользователь передаёт удостоверение; сервис проверяет роль и открывает сессию.",
     "Неверная учётная запись: отказ и повторный вход."),
    ("UC02", "Просмотреть каталог оборудования", "Студент/сотрудник", 3, (1,1,2,0), 22,
     "Выбрать категорию, получить карточки и правила выдачи.",
     "Пустой результат: предложить сбросить фильтр."),
    ("UC03", "Найти доступный интервал", "Студент/сотрудник", 5, (1,1,3,0), 32,
     "Указать предмет и даты; получить свободные интервалы.",
     "Пересечение с бронью: показать ближайшую альтернативу."),
    ("UC04", "Создать заявку на бронь", "Студент/сотрудник", 8, (2,2,3,2), 70,
     "Выбрать интервал, подтвердить правила, сохранить бронь и уведомить владельца.",
     "Коллизия или лимит: отказ с объяснением, без двойной брони."),
    ("UC05", "Изменить или отменить бронь", "Студент/сотрудник", 6, (2,2,2,2), 50,
     "Открыть свою бронь, сменить интервал или отменить, обновить статус.",
     "После начала выдачи изменение запрещено."),
    ("UC06", "Посмотреть мои брони", "Студент/сотрудник", 3, (1,1,2,0), 20,
     "Получить список активных и прошлых броней.",
     "Нет броней: показать пустое состояние."),
    ("UC07", "Подтвердить выдачу оборудования", "Сотрудник пункта выдачи", 7, (2,2,3,2), 55,
     "Найти заявку, проверить личность и комплектность, отметить выдачу.",
     "Неявка или неподходящий статус: выдачу блокировать."),
    ("UC08", "Зарегистрировать возврат", "Сотрудник пункта выдачи", 7, (2,2,3,2), 55,
     "Проверить предмет, отметить возврат и доступность.",
     "Повреждение: отметить инцидент и вывести предмет из доступных."),
    ("UC09", "Управлять карточкой и доступностью", "Администратор", 8, (2,2,3,2), 60,
     "Создать или изменить карточку, правила и окна доступности.",
     "Нельзя удалить предмет с активной бронью."),
    ("UC10", "Управлять правами доступа", "Администратор", 5, (2,2,2,1), 40,
     "Назначить роль сотрудника и сохранить аудит изменения.",
     "Самому себе нельзя снять последнюю роль администратора."),
    ("UC11", "Получить уведомление о статусе", "Студент/сотрудник", 4, (1,2,2,1), 28,
     "После изменения статуса отправить уведомление и записать факт доставки.",
     "Сбой почты: повторить отправку, бронь оставить действительной."),
    ("UC12", "Посмотреть отчёт по использованию", "Администратор", 5, (1,2,3,0), 38,
     "Выбрать период и получить число броней и загрузку оборудования.",
     "Нет данных: нулевой отчёт."),
]

TECH = [
    ("Распределённость",2,2),("Время отклика",1,3),("Эффективность пользователя",1,3),
    ("Сложная обработка",1,2),("Повторное использование",1,2),("Простота установки",.5,2),
    ("Удобство эксплуатации",.5,3),("Переносимость",2,2),("Простота изменений",1,3),
    ("Параллелизм",1,4),("Безопасность",1,4),("Доступ третьих сторон",1,1),
    ("Обучение пользователей",1,2)]
ENV = [
    ("Знание процесса",1.5,3),("Опыт с приложениями",.5,3),("ООП опыт",1,3),
    ("Ведущий аналитик",.5,3),("Мотивация",1,4),("Стабильность требований",2,3),
    ("Частичная занятость",-1,2),("Сложность языка",-1,2)]

def phase3():
    rows = []
    for ix, (code, title, actor, txn, flow, anchor, main, alt) in enumerate(UC):
        e,x,r,w = flow
        weight = 5 if txn <= 3 else (10 if txn <= 7 else 15)
        # Three team-confirmed expert estimates around a shared reference.
        offsets = [(-3,2,1),(2,-2,3),(-2,3,0),(4,-4,2),(-3,2,4),(1,-2,2),
                   (3,-3,2),(-2,4,1),(2,-3,4),(-2,3,1),(1,-2,2),(2,-3,1)]
        estimates = [max(1, anchor + delta) for delta in offsets[ix]]
        rows.append({"id":code,"title":title,"actor":actor,"transactions":txn,
                     "complexity_weight":weight,"E":e,"X":x,"R":r,"W":w,
                     "cfp":e+x+r+w,"main_flow":main,"alternate":alt,
                     "expert_hours":estimates,"consensus_hours":sorted(estimates)[1]})
    uaw = 9 # Three human roles, each a complex graphical/system actor (weight 3).
    uucw = sum(r["complexity_weight"] for r in rows)
    tfactor = sum(weight*rating for _,weight,rating in TECH)
    efactor = sum(weight*rating for _,weight,rating in ENV)
    tcf = .6 + .01*tfactor
    ecf = 1.4 - .03*efactor
    ucp = (uaw + uucw)*tcf*ecf
    cfp = sum(r["cfp"] for r in rows)
    consensus = sum(r["consensus_hours"] for r in rows)
    experts = [sum(r["expert_hours"][k] for r in rows) for k in range(3)]
    return {"uc":rows,"cosmic_total_cfp":cfp,"cosmic_assumed_hours_per_cfp":8,
            "cosmic_effort_hours":cfp*8,"uaw":uaw,"uucw":uucw,"uucp":uaw+uucw,
            "technical_factors":[{"name":n,"weight":w,"rating":r,"product":w*r} for n,w,r in TECH],
            "environment_factors":[{"name":n,"weight":w,"rating":r,"product":w*r} for n,w,r in ENV],
            "technical_sum":tfactor,"environment_sum":efactor,"tcf":tcf,"ecf":ecf,
            "ucp":ucp,"ucp_assumed_hours_per_point":20,"ucp_effort_hours":ucp*20,
            "expert_totals_hours":experts,"consensus_hours":consensus,
            "recommended_budget_hours":math.ceil(max(consensus,cfp*8)*1.2/40)*40}

# Phase 4 concerns the team coursework needed to prepare *phase 5*, whereas
# phase 5 below schedules a planned implementation of the chosen product.
P4 = [
    ("P01","Уточнить объём MVP",2,3,5),("P02","Разбить реализацию на 24 работы",5,7,10),
    ("P03","Проверить длительности работ",4,6,9),("P04","Назначить роли и мощности",3,4,7),
    ("P05","Построить зависимости",4,5,8),("P06","Расчёт ранних и поздних сроков",4,6,9),
    ("P07","Реализовать генератор расписания",8,11,16),("P08","Прогнать правила приоритета",5,7,10),
    ("P09","Проверить ограничения ресурсов",3,5,8),("P10","Сравнить сроки и выбрать план",3,4,7),
    ("P11","Составить RACI и обоснование",3,5,8),("P12","Оформить и проверить отчёт",5,7,11),
]
HISTORY = [
    {"week":1,"start":"2026-09-10","end":"2026-09-16","completed_tasks":4,"hours_per_person":6,"clean_hours":18},
    {"week":2,"start":"2026-09-17","end":"2026-09-23","completed_tasks":5,"hours_per_person":5,"clean_hours":15},
    {"week":3,"start":"2026-09-24","end":"2026-09-30","completed_tasks":3,"hours_per_person":4,"clean_hours":12},
    {"week":4,"start":"2026-10-01","end":"2026-10-07","completed_tasks":4,"hours_per_person":4,"clean_hours":12},
]

PHASE1_LOG_NAMES = [
    "Уточнить концепции и критерии",
    "Провести независимые оценки TOPSIS",
    "Провести парные сравнения МАИ",
    "Проверить полноту и согласованность оценок",
    "Рассчитать нечёткий коллективный TOPSIS",
    "Рассчитать чёткий коллективный МАИ",
    "Сопоставить результаты и выбрать концепцию",
    "Описать исходные данные, расчёты и вывод",
    "Обновить RACI и учёт времени",
]

def reconstruct_task_log():
    """Allocate stated weekly totals to tasks using remembered 3–5 h range.

    These are explicitly reconstructed estimates, not exact historical entries.
    Task identities/week allocation are also reconstructed from the WBS order.
    """
    selections = [
        [(f"F1-{i+1:02d}", PHASE1_LOG_NAMES[i]) for i in range(4)],
        [(f"F1-{i+1:02d}", PHASE1_LOG_NAMES[i]) for i in range(4,9)],
        [(t[0],t[1]) for t in P2[:3]],
        [(t[0],t[1]) for t in P2[3:7]],
    ]
    # Every task is within the remembered 3–5 h range, and each week sums to
    # the confirmed 3-person total of 18/15/12/12 h.
    allocated = [[5,4,5,4],[3,3,3,3,3],[4,4,4],[3,3,3,3]]
    rows=[]
    for week, tasks, hours in zip(HISTORY,selections,allocated):
        assert sum(hours)==week['clean_hours'] and len(tasks)==week['completed_tasks']
        for (code,name),h in zip(tasks,hours):
            rows.append({'week':week['week'],'period_start':week['start'],
                         'period_end':week['end'],'task_id':code,'task_name':name,
                         'clean_hours_estimate':h,'status':'Восстановлено по памяти',
                         'exact_dates_known':False})
    return rows

def quantile_int(values, p):
    values = sorted(values)
    return values[math.ceil(p*len(values))-1]

def phase4():
    rng = random.Random(42024)
    n, reps = len(P4), 50000
    distribution1, distribution2 = [], []
    throughput = [v["completed_tasks"] for v in HISTORY]
    hours = [v["clean_hours"] for v in HISTORY]
    for _ in range(reps):
        remaining, weeks = n, 0
        while remaining > 0:
            remaining -= rng.choice(throughput)
            weeks += 1
        distribution1.append(weeks)
        total = sum(rng.triangular(lo, hi, mode) for _,_,lo,mode,hi in P4)
        weeks = 0
        while total > 0:
            total -= rng.choice(hours)
            weeks += 1
        distribution2.append(weeks)
    def summary(values):
        return {"mean":sum(values)/len(values),"p50":quantile_int(values,.5),
                "p80":quantile_int(values,.8),"p90":quantile_int(values,.9),
                "distribution":{str(k):values.count(k) for k in sorted(set(values))}}
    return {"tasks":[{"id":a,"name":b,"min_h":c,"mode_h":d,"max_h":e} for a,b,c,d,e in P4],
            "history":HISTORY,"replications":reps,"seed":42024,"task_count":n,
            "task_hours_mode_total":sum(t[3] for t in P4),
            "throughput_model":summary(distribution1),"capacity_model":summary(distribution2)}

# Phase 5: 24 implementation activities. Demands are whole people per day.
# The project is a hypothetical full-time team, distinct from the 3 students.
CAPACITY = {"BA":1,"Архитектор":1,"Разработчик":2,"Дизайнер":1,"Тестировщик":1,"DevOps":1}
TASKS5 = [
    ("A01","Согласовать MVP и критерии готовности",3,{"BA":1},[]),
    ("A02","Уточнить процессы выдачи и возврата",3,{"BA":1},["A01"]),
    ("A03","Спроектировать архитектуру и модель данных",4,{"Архитектор":1},["A01"]),
    ("A04","Создать прототип интерфейса",4,{"Дизайнер":1},["A01"]),
    ("A05","Настроить репозиторий и сборку",2,{"DevOps":1},["A03"]),
    ("A06","Подготовить БД и миграции",3,{"Разработчик":1},["A03","A05"]),
    ("A07","Реализовать авторизацию и роли",5,{"Разработчик":1},["A06"]),
    ("A08","Реализовать каталог и карточку",5,{"Разработчик":1},["A04","A06"]),
    ("A09","Реализовать календарь доступности",6,{"Разработчик":1},["A06"]),
    ("A10","Реализовать бронирование и проверку конфликтов",7,{"Разработчик":1},["A07","A09"]),
    ("A11","Реализовать мои брони и отмену",4,{"Разработчик":1},["A10"]),
    ("A12","Реализовать выдачу и возврат",6,{"Разработчик":1},["A02","A10"]),
    ("A13","Реализовать управление оборудованием",5,{"Разработчик":1},["A07","A08"]),
    ("A14","Реализовать уведомления",4,{"Разработчик":1},["A10"]),
    ("A15","Реализовать отчёт об использовании",4,{"Разработчик":1},["A12","A13"]),
    ("A16","Сверстать пользовательские экраны",6,{"Разработчик":1},["A04","A07","A08"]),
    ("A17","Сверстать экраны сотрудника и администратора",5,{"Разработчик":1},["A12","A13"]),
    ("A18","Подготовить тестовые сценарии",4,{"Тестировщик":1},["A02","A04"]),
    ("A19","Провести модульные и API-тесты",6,{"Тестировщик":1},["A10","A11","A12","A13","A14","A15"]),
    ("A20","Провести сквозные и нагрузочные тесты",5,{"Тестировщик":1},["A16","A17","A19"]),
    ("A21","Исправить найденные дефекты",5,{"Разработчик":2},["A20"]),
    ("A22","Подготовить развертывание и резервирование",4,{"DevOps":1},["A05","A15"]),
    ("A23","Провести приёмку с заказчиком",3,{"BA":1},["A21","A22"]),
    ("A24","Выпустить MVP и передать инструкции",2,{"DevOps":1},["A23"]),
]

def critical_path(tasks):
    byid = {t[0]:t for t in tasks}
    succ = {t[0]:[] for t in tasks}
    for code,_,_,_,pred in tasks:
        for p in pred: succ[p].append(code)
    order = []
    remaining = set(byid)
    while remaining:
        eligible = sorted(i for i in remaining if all(p in order for p in byid[i][4]))
        if not eligible: raise ValueError("Cycle in task graph")
        order += eligible
        remaining.difference_update(eligible)
    es, ef = {}, {}
    for i in order:
        es[i] = max([ef[p] for p in byid[i][4]],default=0)
        ef[i] = es[i]+byid[i][2]
    finish = max(ef.values())
    ls, lf = {}, {}
    for i in reversed(order):
        lf[i] = min([ls[j] for j in succ[i]], default=finish)
        ls[i] = lf[i]-byid[i][2]
    free = {i:(min([es[j] for j in succ[i]],default=finish)-ef[i]) for i in byid}
    # The assignment defines grouped priority measures over DIRECT successors.
    gp = {i:byid[i][2]+sum(byid[j][2] for j in succ[i]) for i in byid}
    group_resource = {i:sum(byid[i][3].values())+
                      sum(sum(byid[j][3].values()) for j in succ[i]) for i in byid}
    return {"order":order,"successors":succ,"es":es,"ef":ef,"ls":ls,"lf":lf,
            "free":free,"slack":{i:ls[i]-es[i] for i in byid},
            "group_work":gp,"group_resource":group_resource,"baseline_days":finish}

def schedule(tasks, metrics, rule, seed=0):
    byid = {t[0]:t for t in tasks}
    scheduled = {}
    remaining = set(byid)
    usage = defaultdict(lambda:defaultdict(int))
    rng = random.Random(seed)
    while remaining:
        eligible = [i for i in remaining if all(p in scheduled for p in byid[i][4])]
        if not eligible: raise ValueError("No eligible task")
        def key(i):
            duration, demand = byid[i][2], byid[i][3]
            units = sum(demand.values())
            successors = len(metrics["successors"][i])
            rw = metrics["group_work"][i]
            base = {
                "SLK":(metrics["slack"][i],),
                "FREE":(metrics["free"][i],),
                "LST":(metrics["ls"][i],),
                "LFT":(metrics["lf"][i],),
                "LSTLFT":(metrics["ls"][i]+metrics["lf"][i],),
                "GRPW":(-rw,),
                "LPT":(-duration,),
                "MIS":(-successors,),
                "GRD":(-duration*units,),
                "GRWC":(-units,),
                "GCRWC":(-metrics["group_resource"][i],),
                "ROT":(-sum(need/CAPACITY[role] for role,need in demand.items())/duration,),
                "RANDOM":(rng.random(),),
            }[rule]
            return base + (i,)
        i = min(eligible,key=key)
        _,_,duration,demand,pred = byid[i]
        start = max([scheduled[p][1] for p in pred],default=0)
        while any(usage[d][role]+need > CAPACITY[role]
                  for d in range(start,start+duration) for role,need in demand.items()):
            start += 1
        end = start+duration
        scheduled[i] = (start,end)
        for day in range(start,end):
            for role,need in demand.items(): usage[day][role]+=need
        remaining.remove(i)
    return {"makespan_days":max(v[1] for v in scheduled.values()),
            "start_end":{i:list(v) for i,v in scheduled.items()},"rule":rule}

def workdate(offset, origin=dt.date(2027,1,11)):
    day = origin
    for _ in range(offset):
        day += dt.timedelta(days=1)
        while day.weekday() >= 5: day += dt.timedelta(days=1)
    return day.isoformat()

def phase5():
    m = critical_path(TASKS5)
    rules = ["SLK","FREE","LST","LFT","LSTLFT","GRPW","LPT","MIS",
             "GRD","GRWC","GCRWC","ROT"]
    runs = [schedule(TASKS5,m,r) for r in rules]
    random_runs = [schedule(TASKS5,m,"RANDOM",i) for i in range(100)]
    random_best = min(random_runs,key=lambda x:x["makespan_days"])
    runs.append({**random_best,"rule":"RANDOM (лучший из 100)"})
    best = min(runs,key=lambda x:(x["makespan_days"],rules.index(x["rule"]) if x["rule"] in rules else 99))
    # Verify precedence and resource capacity on the selected schedule.
    used = defaultdict(lambda:defaultdict(int))
    for code,_,duration,demand,pred in TASKS5:
        start,end = best["start_end"][code]
        assert end-start == duration
        assert all(best["start_end"][p][1] <= start for p in pred)
        for day in range(start,end):
            for role,need in demand.items(): used[day][role]+=need
    assert all(v <= CAPACITY[role] for day in used.values() for role,v in day.items())
    rows=[]
    for code,name,duration,demand,pred in TASKS5:
        start,end=best["start_end"][code]
        rows.append({"id":code,"name":name,"duration_days":duration,"demand":demand,
                     "predecessors":pred,"es":m["es"][code],"ls":m["ls"][code],
                     "slack":m["slack"][code],"free":m["free"][code],
                     "start_day":start,"end_day":end,"start_date":workdate(start),
                     "finish_date":workdate(end-1)})
    return {"tasks":rows,"capacity":CAPACITY,"start_date":"2027-01-11",
            "baseline_days":m["baseline_days"],"best_rule":best["rule"],
            "makespan_days":best["makespan_days"],"finish_date":workdate(best["makespan_days"]-1),
            "heuristics":[{"rule":x["rule"],"days":x["makespan_days"]} for x in runs],
            "random_runs":100,"total_person_days":sum(t[2]*sum(t[3].values()) for t in TASKS5),
            "critical_tasks":[i for i in m["order"] if m["slack"][i]==0]}

def main():
    data = {"status":"Оценки согласованы командой; недельные итоги предоставлены пользователем; часы по задачам восстановлены в диапазоне 3–5 ч",
            "team":PEOPLE,"phase2":optimize_assignment(P2),"phase3":phase3(),
            "phase4":phase4(),"phase5":phase5(),"reconstructed_log":reconstruct_task_log()}
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"p2":data["phase2"]["loads"],"p3":{
        k:data["phase3"][k] for k in ["cosmic_total_cfp","ucp","consensus_hours","recommended_budget_hours"]},
        "p4":[data["phase4"][k]["p80"] for k in ["throughput_model","capacity_model"]],
        "p5":[data["phase5"][k] for k in ["baseline_days","best_rule","makespan_days","finish_date"]]},ensure_ascii=False))

if __name__ == "__main__": main()
