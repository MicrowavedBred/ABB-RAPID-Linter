!--1. Module Structure--

!Every RAPID program consists of --Modules--. The entry point is usually the `main` procedure within a module.

MODULE ModuleName
    ! Data Declarations (CONST, VAR, PERS) go here
    
    ! Procedure Declarations
    PROC main()
        ! The program starts here
    ENDPROC
    
ENDMODULE


!--2. Data Declarations--

!RAPID distinguishes between three storage types:

!--VAR--: Standard variable (resets when procedure/module is re-initialized).
!--PERS--: Persistent variable (retains value between program stops/starts).
!--CONST--: Constant (cannot be changed by the program).

!--Common Data Types--

! Type        | Description                   | Example                            |
! ----------------------------------------------------------------------------------
! `num`       | Numeric (integer or float)    | `VAR num count := 0;`              |
! `bool`      | Boolean (TRUE/FALSE)          | `VAR bool active := TRUE;`         |
! `string`    | Text string                   | `VAR string text := "Hello";`      |
! `robtarget` | Robot position (x,y,z,q1..q4) | `CONST robtarget p1 := [...]`      |
! `tooldata`  | TCP (Tool Center Point) data  | `PERS tooldata myGripper := [...]` |
! `wobjdata`  | Work Object data              | `PERS wobjdata fixture1 := [...]`  |

!--Declaration Syntax--

! Syntax: STORAGE_TYPE DATA_TYPE name := value;

VAR num counter := 0; 
CONST num max_speed := 1000;
PERS bool isFinished := FALSE;



!--3. Flow Control & Logic--

!--IF ... THEN ... ELSE--

!Note the use of the single `=` for comparison.

IF reg1 = 5 THEN
    ! Do something
    SetDO doSignal, 1;
ELSEIF reg1 > 5 THEN
    ! Do something else
    SetDO doSignal, 0;
ELSE
    ! Default action
    TPWrite "Invalid Value";
ENDIF


!--TEST (Switch Case)--

! Used for checking one variable against multiple values.

TEST part_type
    CASE 1:
        CallRoutine1;
    CASE 2, 3:
        ! Cases can be grouped
        CallRoutine2;
    DEFAULT:
        Stop;
ENDTEST


!--Loops--

!--FOR Loop-- (Counted iteration)

FOR i FROM 1 TO 10 DO
    reg1 := reg1 + i;
ENDFOR


!--WHILE Loop-- (Conditional iteration)

WHILE DI10_Input = 1 DO
    WaitTime 0.1;
ENDWHILE


!--4. Motion Instructions--
!
!Standard moves require a --Point--, --Speed--, --Zone-- (corner path), and --Tool--.
!
!* `MoveJ`: Joint move (quickest, path not linear).
!* `MoveL`: Linear move (straight line TCP path).
!* `MoveC`: Circular move.

! Syntax: MoveL Target, Speed, Zone, Tool;

MoveJ pHome, v1000, z50, tool0;
MoveL pPick, v500, fine, myGripper;

! Move with Work Object (WObj) reference
MoveL pPlace, v200, z10, myGripper \WObj:=fixture1;


!--Note:-- `fine` zone means the robot stops exactly at the point. `z10`, `z50`, etc., allow the robot to corner-cut for smooth motion.

!--5. I/O & Communication--

! Digital Outputs
Set doClamp;          ! Sets signal to 1 (True)
Reset doClamp;        ! Sets signal to 0 (False)
SetDO doClamp, 1;     ! Specific value assignment
PulseDO doClamp;      ! Pulses high then low

! Digital Inputs (Waiting)
WaitDI diSensor, 1;   ! Wait until diSensor becomes 1

! Time
WaitTime 1.5;         ! Pause program for 1.5 seconds

! FlexPendant Output
TPWrite "Cycle Completed: " \Num:=cycleCount;
TPReadNum reg1, "Enter part quantity";



!--6. Routines (PROC and FUNC)--

!--PROC (Procedure)--

!A sub-program that performs actions but does not return a value.

! Definition
PROC PickPart(num pickHeight)
    MoveJ pAbovePick, v1000, z50, toolGripper;
    
    ! Offset the pick position by Z height
    MoveL Offs(pPickLoc, 0, 0, pickHeight), v200, fine, toolGripper;
    
    Set doVacuum;
    WaitTime 0.5;
    MoveL pAbovePick, v500, z10, toolGripper;
ENDPROC

! Usage (Calling the PROC)
PROC main()
    PickPart 20;  ! Calls routine with argument 20
ENDPROC


!--FUNC (Function)--

!A sub-program that performs calculations and --must-- return a value.

! Definition
FUNC num CalculateArea(num length, num width)
    VAR num result;
    result := length * width;
    RETURN result;
ENDFUNC

! Usage
PROC main()
    VAR num totalArea;
    totalArea := CalculateArea(10, 5);
    TPWrite "Area is: " \Num:=totalArea;
ENDPROC



!--7. Common Built-in Functions--

! Function              | Usage                            | Description                                                                          |
! ----------------------------------------------------------------------------------------------------------
! `Offs(p, x, y, z)`    | `MoveL Offs(p1, 0, 0, 10)...`    | Returns a robtarget offset by X, Y, Z relative to the work object.                   |
! `RelTool(p, x, y, z)` | `MoveL RelTool(p1, 0, 0, 10)...` | Returns a robtarget offset relative to the --Tool-- frame (e.g., move forward in Z). |
! `CRobT()`             | `pCurrent := CRobT();`           | Reads the current robot position.                                                    |
! `StrLen(str)`         | `len := StrLen(s1);`             | Returns length of a string.                                                          |
! `ValToString(val)`    | `s1 := ValToString(reg1);`       | Converts a number to a string.                                                       |


!--8. Error Handling--

!RAPID uses a standard error handler at the bottom of a routine.

PROC MoveToPick()
    MoveL pPick, v1000, fine, tool0;
    
ERROR
    IF ERRNO = ERR_COLL_STOP THEN
        ! Handle collision
        StorePath;
        MoveL Offs(pPick, 0, 0, 50), v100, fine, tool0;
        RestoPath;
        RETRY;  
		! Tries the instruction that failed again
    ENDIF
ENDPROC
