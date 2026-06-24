import streamlit as st
from datetime import datetime, date, time, timedelta

st.set_page_config(page_title="Compensatory Rest Calculator")

THRESHOLD = timedelta(hours=1, minutes=30)
REST_REQUIRED = timedelta(hours=9)

WINDOW_START = time(0, 0)
WINDOW_END = time(5, 0)


def parse_time_input(time_str):
    try:
        return datetime.strptime(time_str.strip(), "%H:%M").time()
    except:
        return None


def combine(d, t):
    return datetime.combine(d, t)


def overlap_interval(start1, end1, start2, end2):
    start = max(start1, start2)
    end = min(end1, end2)

    if end <= start:
        return None

    return start, end


def qualifying_segment(start, end, window_start, window_end):

    overlap = overlap_interval(start, end, window_start, window_end)

    if not overlap:
        return None

    seg_start, seg_end = overlap

    if seg_end - seg_start >= THRESHOLD:
        return seg_start, seg_end

    return None


def find_latest_qualifying(efforts, window_start, window_end):

    qualifying = []

    for start, end in efforts:

        segment = qualifying_segment(start, end, window_start, window_end)

        if segment:
            qualifying.append((start, end, segment))

    if not qualifying:
        return None

    qualifying.sort(key=lambda x: x[1])
    return qualifying[-1]


st.title("Compensatory Rest Calculator")

st.write(
    "Calculate earliest allowed start time when compensatory rest is triggered "
    "by night work between 00:00–05:00."
)

shift_date = st.date_input("Date of next regular shift", value=date.today())

regular_start_str = st.text_input("Regular shift start (HH:MM)", value="07:00")

regular_start = parse_time_input(regular_start_str)

if not regular_start:
    st.error("Regular shift start must be written as HH:MM")
    st.stop()

st.header("Night work efforts")

if "efforts" not in st.session_state:
    st.session_state.efforts = []

if st.button("Add work effort"):
    st.session_state.efforts.append({"start": "00:00", "end": "01:30"})


for i, effort in enumerate(st.session_state.efforts):

    col1, col2, col3 = st.columns([3,3,1])

    with col1:
        effort["start"] = st.text_input(
            f"Start #{i+1} (HH:MM)",
            value=effort["start"],
            key=f"start{i}"
        )

    with col2:
        effort["end"] = st.text_input(
            f"End #{i+1} (HH:MM)",
            value=effort["end"],
            key=f"end{i}"
        )

    with col3:
        if st.button("Remove", key=f"remove{i}"):
            st.session_state.efforts.pop(i)
            st.rerun()


if st.button("Calculate earliest allowed start time"):

    night_date = shift_date - timedelta(days=1)

    # Night window 00:00–05:00 same night as disturbance
    window_start = combine(shift_date, WINDOW_START)
    window_end = combine(shift_date, WINDOW_END)

    efforts = []

    for e in st.session_state.efforts:

        start_time = parse_time_input(e["start"])
        end_time = parse_time_input(e["end"])

        if not start_time or not end_time:
            st.error("All times must be written in HH:MM format.")
            st.stop()

        start = combine(night_date, start_time)
        end = combine(night_date, end_time)

        if end <= start:
            end += timedelta(days=1)

        efforts.append((start, end))

    latest = find_latest_qualifying(efforts, window_start, window_end)

    regular_start_dt = combine(shift_date, regular_start)

    st.subheader("Result")

    if not latest:

        st.warning(
            "No qualifying work effort of at least 1.5 hours within 00:00–05:00."
        )

        st.write(
            f"Regular start time applies: **{regular_start_dt.strftime('%H:%M')}**"
        )

    else:

        start, end, segment = latest
        seg_start, seg_end = segment

        rest_start = end
        earliest_start = rest_start + REST_REQUIRED

        st.write("Qualifying work segment within 00:00–05:00:")
        st.write(f"{seg_start.strftime('%H:%M')} – {seg_end.strftime('%H:%M')}")

        st.write("Last qualifying work effort:")
        st.write(f"{start.strftime('%H:%M')} – {end.strftime('%H:%M')}")

        st.write("Required rest period:")
        st.write(f"{rest_start.strftime('%H:%M')} – {earliest_start.strftime('%H:%M')}")

        if earliest_start > regular_start_dt:

            st.success(
                f"Earliest allowed start time: **{earliest_start.strftime('%H:%M')}**"
            )

        else:

            st.success(
                f"Regular shift start applies: **{regular_start_dt.strftime('%H:%M')}**"
            )
