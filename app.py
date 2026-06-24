import streamlit as st
from datetime import datetime, date, timedelta

THRESHOLD_MINUTES = 90
REQUIRED_REST_MINUTES = 540

def parse_time(t):
    try:
        return datetime.strptime(t, "%H:%M")
    except:
        return None

st.title("Compensatory Rest Calculator")

shift_date = st.date_input("Date of next regular shift", value=date.today())

regular_start_str = st.text_input("Regular shift start (HH:MM)", value="07:00")
regular_start = parse_time(regular_start_str)

if not regular_start:
    st.error("Regular shift start must be HH:MM")
    st.stop()

st.header("Night disturbances (00:00–05:00)")

if "efforts" not in st.session_state:
    st.session_state.efforts = []

if st.button("Add disturbance"):
    st.session_state.efforts.append({"start":"00:00","end":"01:00"})

for i, effort in enumerate(st.session_state.efforts):

    col1,col2,col3 = st.columns([3,3,1])

    with col1:
        effort["start"] = st.text_input(
            f"Start #{i+1} (HH:MM)",
            value=effort["start"],
            key=f"s{i}"
        )

    with col2:
        effort["end"] = st.text_input(
            f"End #{i+1} (HH:MM)",
            value=effort["end"],
            key=f"e{i}"
        )

    with col3:
        if st.button("Remove", key=f"r{i}"):
            st.session_state.efforts.pop(i)
            st.rerun()


if st.button("Calculate"):

    disturbances = []

    for e in st.session_state.efforts:

        start = parse_time(e["start"])
        end = parse_time(e["end"])

        if not start or not end:
            st.error("Times must be HH:MM")
            st.stop()

        start_minutes = start.hour*60 + start.minute
        end_minutes = end.hour*60 + end.minute

        if end_minutes <= start_minutes:
            st.error("End time must be after start time")
            st.stop()

        disturbances.append((start_minutes,end_minutes))

    disturbances.sort()

    qualifying = False

    for s,e in disturbances:
        if e-s >= THRESHOLD_MINUTES:
            qualifying = True

    if not qualifying:

        st.warning("No disturbance ≥ 1.5 hours.")
        st.write(f"Regular start applies: {regular_start_str}")
        st.stop()

    rest_taken = 0

    for i in range(len(disturbances)-1):

        prev_end = disturbances[i][1]
        next_start = disturbances[i+1][0]

        gap = next_start - prev_end

        if gap > 0:
            rest_taken += gap

    last_end = disturbances[-1][1]

    remaining_rest = REQUIRED_REST_MINUTES - rest_taken

    if remaining_rest < 0:
        remaining_rest = 0

    earliest_start_minutes = last_end + remaining_rest

    hours = earliest_start_minutes // 60
    minutes = earliest_start_minutes % 60

    earliest_start = f"{hours:02}:{minutes:02}"

    st.subheader("Result")

    st.write(f"Rest already taken between disturbances: {rest_taken} minutes")
    st.write(f"Remaining rest required: {remaining_rest} minutes")

    if earliest_start > regular_start_str:
        st.success(f"Earliest allowed start time: {earliest_start}")
    else:
        st.success(f"Regular start time applies: {regular_start_str}")
