import streamlit as st
from datetime import datetime, date

THRESHOLD = 90
REST_REQUIRED = 540

WINDOW_START = 0
WINDOW_END = 300


def parse_time(t):
    try:
        dt = datetime.strptime(t, "%H:%M")
        minutes = dt.hour * 60 + dt.minute

        if minutes >= 720:
            minutes -= 1440

        return minutes

    except:
        return None


def clip_to_window(start, end):

    start = max(start, WINDOW_START)
    end = min(end, WINDOW_END)

    if end <= start:
        return None

    return start, end


def minutes_to_time(m):

    h = m // 60
    m = m % 60

    if h < 0:
        h += 24

    return f"{h:02}:{m:02}"


st.title("Compensatory Rest Calculator")

shift_date = st.date_input("Date of next regular shift", value=date.today())

regular_start_str = st.text_input("Regular shift start (HH:MM)", value="07:00")
regular_start = parse_time(regular_start_str)

if regular_start is None:
    st.error("Regular shift start must be HH:MM")
    st.stop()

st.header("Night disturbances")

if "efforts" not in st.session_state:
    st.session_state.efforts = []

if st.button("Add disturbance"):
    st.session_state.efforts.append({"start": "00:00", "end": "01:00"})


for i, effort in enumerate(st.session_state.efforts):

    col1, col2, col3 = st.columns([3,3,1])

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

        if start is None or end is None:
            st.error("Times must be HH:MM")
            st.stop()

        if end <= start:
            end += 1440

        clipped = clip_to_window(start, end)

        if clipped:
            disturbances.append(clipped)

    disturbances.sort()

    if not disturbances:
        st.warning("No disturbances occurred between 00:00 and 05:00.")
        st.stop()

    qualifying = any((e - s) >= THRESHOLD for s, e in disturbances)

    if not qualifying:
        st.warning("No disturbance ≥ 1.5 hours within 00:00–05:00.")
        st.write(f"Regular start applies: {regular_start_str}")
        st.stop()

    rest_taken = 0

    for i in range(len(disturbances) - 1):

        prev_end = disturbances[i][1]
        next_start = disturbances[i + 1][0]

        gap = next_start - prev_end

        if gap > 0:
            rest_taken += gap

    last_end = disturbances[-1][1]

    remaining_rest = REST_REQUIRED - rest_taken

    if remaining_rest < 0:
        remaining_rest = 0

    earliest_start = last_end + remaining_rest

    st.subheader("Result")

    st.write(f"Rest already taken between disturbances: {rest_taken} minutes")
    st.write(f"Remaining rest required: {remaining_rest} minutes")

    if earliest_start > regular_start:

        st.success(
            f"Earliest allowed start time: {minutes_to_time(earliest_start)}"
        )

    else:

        st.success(
            f"Regular shift start applies: {regular_start_str}"
        )
